# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

# pylint: disable=odoo-addons-relative-import
from odoo.addons.stock_inventory_revaluation.tests.common import (
    TestStockInventoryRevaluationCommon,
)


@tagged("post_install", "-at_install")
class TestStockInventoryRevaluation(TestStockInventoryRevaluationCommon):
    def test_01_stock_inventory_revaluation(self):
        """
        Revaluate FIFO and AVG products that partially left the company
        """
        product_fifo = self._create_product("FIFO", 10, self.categ_real_time_fifo)
        product_avg = self._create_product("AVG", 20, self.categ_real_time_avg)
        self.assertEqual(product_fifo.value_svl, 0)
        self.assertEqual(product_fifo.quantity_svl, 0)
        self.assertEqual(product_avg.value_svl, 0)
        self.assertEqual(product_avg.quantity_svl, 0)

        # I create 2 picking moving those products in and out. Moves in:
        moves = [
            {
                "product": product_fifo,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "qty": 10,
                "location_dest_id": self.warehouse.lot_stock_id.id,
            },
            {
                "product": product_avg,
                "qty": 10,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "location_dest_id": self.warehouse.lot_stock_id.id,
            },
        ]
        picking_type_id = self.warehouse.in_type_id.id
        picking_to_revaluate_1 = self._create_picking(picking_type_id, moves)

        # Confirm and assign picking
        self._do_picking(picking_to_revaluate_1)
        # Move some qty out in another picking
        moves = [
            {
                "product": product_fifo,
                "location_dest_id": self.ref("stock.stock_location_customers"),
                "qty": 5,
                "location_id": self.warehouse.lot_stock_id.id,
            },
            {
                "product": product_avg,
                "qty": 5,
                "location_dest_id": self.ref("stock.stock_location_customers"),
                "location_id": self.warehouse.lot_stock_id.id,
            },
        ]
        picking_type_id = self.warehouse.out_type_id.id
        picking_to_revaluate_2 = self._create_picking(picking_type_id, moves)

        # Confirm and assign picking
        self._do_picking(picking_to_revaluate_2)

        # Check the value is the expected (this is still standard, just checking)
        self.assertEqual(product_fifo.value_svl, 50)
        self.assertEqual(product_fifo.quantity_svl, 5)
        self.assertEqual(product_avg.value_svl, 100)
        self.assertEqual(product_avg.quantity_svl, 5)

        # I create a bill and a revaluation at double price
        vendor = self.partner_model.create({"name": "Vendor"})
        bill = self._create_bill(
            "in_invoice", vendor, [product_fifo, product_avg], [10, 10], [20, 40]
        )
        bill._post()
        bill.button_revaluate()
        revaluation_ids = bill.action_view_inventory_revaluation_lines()["domain"][0][2]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = bill
        # Calling the onchange directly cannot save the form of existing object
        # and get the changes applied in the same variable
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[0]
        revaluation.onchange_add_from_stock_move()
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[1]
        revaluation.onchange_add_from_stock_move()

        # I check the revaluation lines
        reval1 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_fifo
        )
        reval2 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_avg
        )
        self.assertEqual(reval1.additional_value, 100)
        self.assertEqual(reval2.additional_value, 200)

        # I confirm the revaluation that creates the layers and account moves
        revaluation.button_validate()

        # I check the journal entry
        self.assertEqual(revaluation.state, "done")
        self.assertTrue(revaluation.account_move_id)

        revaluation_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            ).mapped("debit")
        )
        product_value = abs(product_fifo.value_svl) + abs(product_avg.value_svl)
        self.assertEqual(revaluation_value, product_value)

        self.assertEqual(
            len(picking_to_revaluate_1.move_lines[0].stock_valuation_layer_ids), 2
        )
        self.assertEqual(
            len(picking_to_revaluate_1.move_lines[1].stock_valuation_layer_ids), 2
        )
        # Test the interim accounts and COGS account values
        interim_received_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_in"]
            ).mapped("balance")
        )
        # The additional interim received should match the overall additional value
        # Excluding what is was delivered
        # 10*10 + 20 *10 (negative because is a credit)
        self.assertEqual(interim_received_value, -300)
        interim_delivered_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_out"]
            ).mapped("balance")
        )
        interim_delivered_debit = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_out"]
            ).mapped("debit")
        )
        # The additional interim delivered is balanced but there are debit and credit
        # for the same value
        # revaluated price: 10*5 + 20*5
        self.assertEqual(interim_delivered_value, 0)
        self.assertEqual(interim_delivered_debit, 150)
        # The additional COGS is for the qty delivered and the additional value
        # revaluated price: 10*5 + 20*5
        cogs_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_expense"]
            ).mapped("balance")
        )
        self.assertEqual(cogs_value, 150)
        # Check the standard price
        self.assertEqual(product_fifo.standard_price, 10.0)
        self.assertEqual(product_avg.standard_price, 40.0)
        # Test it is late to cancel
        with self.assertRaises(UserError):
            revaluation.button_cancel()

    def test_02_stock_inventory_revaluation_credit_note(self):
        """
        Revaluate and revaluate back to the original value with a refund
        """
        product_fifo = self._create_product("FIFO", 10, self.categ_real_time_fifo)
        # I create 1 picking incoming only
        moves = [
            {
                "product": product_fifo,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "qty": 10,
                "location_dest_id": self.warehouse.lot_stock_id.id,
            },
        ]
        picking_type_id = self.warehouse.in_type_id.id
        picking_to_revaluate_1 = self._create_picking(picking_type_id, moves)
        self._do_picking(picking_to_revaluate_1)
        vendor = self.partner_model.create({"name": "Vendor"})
        bill = self._create_bill("in_invoice", vendor, [product_fifo], [10], [20])
        bill._post()
        bill.button_revaluate()
        revaluation_ids = bill.action_view_inventory_revaluation_lines()["domain"][0][2]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = bill
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[0]
        revaluation.onchange_add_from_stock_move()

        # I check the revaluation lines
        reval1 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_fifo
        )
        self.assertEqual(reval1.additional_value, 100)
        # I confirm the revaluation that creates the layers and account moves
        revaluation.button_validate()
        # I check the revaluation is performed
        # Test the valuation is 10 units @ 20 (another 100$)
        additional_valuation_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            ).mapped("balance")
        )
        self.assertEqual(additional_valuation_value, 100)
        # Now I do a refund that will revaluate back to the price it was before
        refund = self._create_bill("in_refund", vendor, [product_fifo], [10], [10])
        refund.button_revaluate()
        revaluation_ids = refund.action_view_inventory_revaluation_lines()["domain"][0][
            2
        ]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = refund
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[0]
        revaluation.onchange_add_from_stock_move()
        # I check the revaluation lines
        reval1 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_fifo
        )
        # The additional value is the value added on the refund, that is 10*10
        self.assertEqual(reval1.additional_value, -100)
        # Test the valuation is back to are 10 units @ 10 (added -100 $ value)
        revaluation.button_validate()
        additional_valuation_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            ).mapped("balance")
        )
        self.assertEqual(additional_valuation_value, -100)

    def test_03_stock_inventory_revaluation_multi_currency(self):
        """
        Revaluate with a vendor bill with different currency than company currency
        """
        self.env.company.currency_id = self.USD
        self._create_currency_rate(self.USD, "2000-01-01", 1.0)
        self._create_currency_rate(self.EUR, "2000-01-01", 0.5)
        product_fifo = self._create_product("FIFO 3", 10, self.categ_real_time_fifo)
        # I create 1 picking incoming only
        moves = [
            {
                "product": product_fifo,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "qty": 10,
                "location_dest_id": self.warehouse.lot_stock_id.id,
            },
        ]
        picking_type_id = self.warehouse.in_type_id.id
        picking_to_revaluate_1 = self._create_picking(picking_type_id, moves)
        self._do_picking(picking_to_revaluate_1)
        vendor = self.partner_model.create({"name": "Vendor"})
        # I revaluate to be double (10 EUR instead of USD)
        bill = self._create_bill(
            "in_invoice", vendor, [product_fifo], [10], [10], self.EUR
        )
        self.assertEqual(bill.invoice_line_ids.price_unit, 10)
        bill._post()
        bill.button_revaluate()
        revaluation_ids = bill.action_view_inventory_revaluation_lines()["domain"][0][2]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = bill
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[0]
        revaluation.onchange_add_from_stock_move()

        # I check the revaluation lines
        reval1 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_fifo
        )
        self.assertEqual(reval1.additional_value, 100)
        # I confirm the revaluation that creates the layers and account moves
        revaluation.button_validate()
        # I check the revaluation is performed
        # Test the valuation is 10 units @ 10 EUR = 20 USD TOTAL 100
        additional_valuation_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            ).mapped("balance")
        )
        self.assertEqual(additional_valuation_value, 100)

    def test_04_partial_invoice(self):
        """
        Revaluate FIFO two times in partial invoices
        """
        product_fifo = self._create_product("FIFO", 15, self.categ_real_time_fifo)
        product_avg = self._create_product("AVG", 15, self.categ_real_time_avg)

        # I create 2 picking moving those products in and out. Moves in:
        moves = [
            {
                "product": product_fifo,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "qty": 10,
                "location_dest_id": self.warehouse.lot_stock_id.id,
            },
            {
                "product": product_avg,
                "qty": 10,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "location_dest_id": self.warehouse.lot_stock_id.id,
            },
        ]
        picking_type_id = self.warehouse.in_type_id.id
        picking_to_revaluate_1 = self._create_picking(picking_type_id, moves)

        # Confirm and assign picking
        self._do_picking(picking_to_revaluate_1)

        # Check the value is the expected (this is still standard, just checking)
        self.assertEqual(product_fifo.value_svl, 150)
        self.assertEqual(product_fifo.quantity_svl, 10)
        self.assertEqual(product_avg.value_svl, 150)
        self.assertEqual(product_avg.quantity_svl, 10)

        # I create a partial bill for a higher price
        vendor = self.partner_model.create({"name": "Vendor"})
        bill = self._create_bill(
            "in_invoice", vendor, [product_fifo, product_avg], [9, 9], [16, 16]
        )
        bill._post()
        bill.button_revaluate()
        revaluation_ids = bill.action_view_inventory_revaluation_lines()["domain"][0][2]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = bill
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[0]
        revaluation.onchange_add_from_stock_move()
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[1]
        revaluation.onchange_add_from_stock_move()

        # I check the revaluation lines
        reval1 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_fifo
        )
        reval2 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_avg
        )
        # The additional value is (15+16*9) - 150
        self.assertEqual(reval1.additional_value, 9)
        self.assertEqual(reval2.additional_value, 9)

        # I confirm the revaluation that creates the layers and account moves
        revaluation.button_validate()
        # Check the standard price, fifo not updated
        self.assertEqual(product_fifo.standard_price, 15.0)
        # 1 unit @ 15 + 9 Units @ 16
        self.assertEqual(product_avg.standard_price, 15.9)
        # I check the journal entry
        self.assertEqual(revaluation.state, "done")
        self.assertTrue(revaluation.account_move_id)
        account_value_fifo = sum(
            self.account_move_line_model.search([("product_id", "=", product_fifo.id)])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            )
            .mapped("debit")
        )
        account_value_avg = sum(
            self.account_move_line_model.search([("product_id", "=", product_avg.id)])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            )
            .mapped("debit")
        )
        revaluation_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            ).mapped("debit")
        )
        product_value = abs(product_fifo.value_svl) + abs(product_avg.value_svl)
        self.assertEqual(revaluation_value, 18)
        self.assertEqual(product_value, account_value_avg + account_value_fifo)
        self.assertEqual(account_value_fifo, 159)
        self.assertEqual(account_value_avg, 159)

        # The value should be 16*9+15*1 in both products
        self.assertEqual(product_fifo.value_svl, 159)
        self.assertEqual(product_avg.value_svl, 159)
        # create a bill for the qty left, at the same price than the original bill
        bill = self._create_bill(
            "in_invoice", vendor, [product_fifo, product_avg], [1, 1], [16, 16]
        )
        bill._post()
        bill.button_revaluate()
        revaluation_ids = bill.action_view_inventory_revaluation_lines()["domain"][0][2]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = bill
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[0]
        revaluation.onchange_add_from_stock_move()
        revaluation.add_from_stock_move = picking_to_revaluate_1.move_lines[1]
        revaluation.onchange_add_from_stock_move()

        # I check the revaluation lines
        reval1 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_fifo
        )
        reval2 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_avg
        )
        # The additional value is (16+16*9) - 159 = 1
        self.assertEqual(reval1.additional_value, 1)
        self.assertEqual(reval2.additional_value, 1)

        # I confirm the revaluation that creates the layers and account moves
        revaluation.button_validate()
        # The value should be 160 on both products
        self.assertEqual(product_fifo.value_svl, 160)
        self.assertEqual(product_avg.value_svl, 160)
        # Finally, check the standard price
        self.assertEqual(product_fifo.standard_price, 15.0)
        self.assertEqual(product_avg.standard_price, 16.0)

    def test_05_stock_inventory_revaluation_credit_no_revaluate(self):
        """
        Do a credit note for a partial quantity (after a return) and do not create
        revaluation, it should not as long as the price of the refund should be the
        same as the original
        """
        product_avg = self._create_product("AVG80", 10, self.categ_real_time_avg)
        # I create 1 picking incoming only
        moves = [
            {
                "product": product_avg,
                "location_id": self.ref("stock.stock_location_suppliers"),
                "qty": 10,
                "location_dest_id": self.warehouse.lot_stock_id.id,
            },
        ]
        picking_type_id = self.warehouse.in_type_id.id
        picking_to_revaluate_1 = self._create_picking(picking_type_id, moves)
        self._do_picking(picking_to_revaluate_1)
        vendor = self.partner_model.create({"name": "Vendor"})
        # create a bill with normal price
        bill = self._create_bill("in_invoice", vendor, [product_avg], [10], [10])
        bill._post()
        # We return half of the quantity
        stock_return_picking_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=picking_to_revaluate_1.ids,
                active_id=picking_to_revaluate_1.ids[0],
                active_model="stock.picking",
            )
        )
        stock_return_picking = stock_return_picking_form.save()
        stock_return_picking.product_return_moves.quantity = 5
        stock_return_picking_action = stock_return_picking.create_returns()
        return_pick = self.env["stock.picking"].browse(
            stock_return_picking_action["res_id"]
        )
        return_pick.move_lines[0].move_line_ids[0].qty_done = 5
        return_pick.button_validate()
        # Now I do a refund that will revaluate half qty at half price
        # so the price of the other half should increase
        refund = self._create_bill("in_refund", vendor, [product_avg], [5], [10])
        refund.button_revaluate()
        revaluation_ids = refund.action_view_inventory_revaluation_lines()["domain"][0][
            2
        ]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = refund
        revaluation.add_from_stock_move = return_pick.move_lines[0]
        revaluation.onchange_add_from_stock_move()
        # I check the revaluation lines
        reval1 = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_avg
        )
        # The additional value is the value added on the refund is nothing
        self.assertEqual(reval1.additional_value, 0)
        revaluation.button_validate()
        additional_valuation_value = sum(
            revaluation.account_move_id.line_ids.filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
            ).mapped("balance")
        )
        # Test that there is no change
        self.assertEqual(additional_valuation_value, 0)
        self.assertEqual(product_avg.value_svl, 50)
        self.assertEqual(product_avg.standard_price, 10.0)
