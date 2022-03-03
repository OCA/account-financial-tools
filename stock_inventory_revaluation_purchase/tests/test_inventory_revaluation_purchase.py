# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.stock_inventory_revaluation.tests.common import (
    TestStockInventoryRevaluationCommon,
)


@tagged("post_install", "-at_install")
class TestStockInventoryRevaluationPurchase(TestStockInventoryRevaluationCommon):
    @classmethod
    def create_purchase_order(cls, vendor, product, qty, price):
        po = cls.env["purchase.order"].create(
            {
                "partner_id": vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "name": product.name,
                            "product_qty": qty,
                            "price_unit": price,
                            "product_uom": product.uom_id.id,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        return po

    def test_01_stock_inventory_revaluation_purchase(self):
        """
        Revaluate an incoming from a purchase order and check the PO info is passed
        """
        product_buy = self._create_product("FIFO", 10, self.categ_real_time_fifo)

        # I create a PO and receive it
        vendor = self.partner_model.create({"name": "Vendor"})
        po = self.create_purchase_order(vendor, product_buy, 10.0, 10.0)
        po.button_confirm()
        # Confirm and assign picking
        self._do_picking(po.picking_ids)

        # Check the value is the expected (this is still standard, just checking)
        self.assertEqual(product_buy.value_svl, 100)

        # I create a bill and a revaluation at double price
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = vendor
        move_form.purchase_id = po
        move_form.invoice_date = fields.Datetime.now()
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 20.0
        bill = move_form.save()
        bill.action_post()
        po.flush()
        bill.button_revaluate()
        revaluation_ids = bill.action_view_inventory_revaluation_lines()["domain"][0][2]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = bill
        # This will compute from the picking of the PO
        revaluation.compute_inventory_revaluation()

        # I check the revaluation lines
        reval = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_buy
        )
        self.assertEqual(reval.additional_value, 100)

        # I confirm the revaluation
        revaluation.button_validate()

        # I check the journal entry has the PO line and the value is ok
        self.assertEqual(revaluation.state, "done")
        self.assertTrue(revaluation.account_move_id)
        aml_valuation = (
            self.env["account.move.line"]
            .search([])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
                and aml.product_id == product_buy
            )
        )
        for aml in aml_valuation:
            self.assertEqual(aml.purchase_line_id, po.order_line[0])
        acc_value = sum(aml_valuation.mapped("balance"))
        product_value = abs(product_buy.value_svl)
        self.assertEqual(product_value, acc_value)
        self.assertEqual(len(po.picking_ids.move_lines[0].stock_valuation_layer_ids), 2)

    def test_02_automation(self):
        """
        Test revaluation is performed when company is revaluation automated
        """
        self.env.user.company_id.revaluation_auto_created = True
        product_buy = self._create_product("FIFO 2", 10, self.categ_real_time_fifo)

        # I create a PO and receive it
        vendor = self.partner_model.create({"name": "Vendor"})
        po = self.create_purchase_order(vendor, product_buy, 10.0, 10.0)
        po.button_confirm()
        # Confirm and assign picking
        self._do_picking(po.picking_ids)

        # Check the value is the expected (this is still standard, just checking)
        self.assertEqual(product_buy.value_svl, 100)

        # I create a bill and a revaluation at double price
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = vendor
        move_form.purchase_id = po
        move_form.invoice_date = fields.Datetime.now()
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 20.0
        bill = move_form.save()
        bill.action_post()
        po.flush()

        # I check the revaluation lines
        aml_valuation = (
            self.env["account.move.line"]
            .search([])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
                and aml.product_id == product_buy
            )
        )
        for aml in aml_valuation:
            self.assertEqual(aml.purchase_line_id, po.order_line[0])
        acc_value = sum(aml_valuation.mapped("balance"))
        product_value = abs(product_buy.value_svl)
        self.assertEqual(product_value, acc_value)
        self.assertEqual(len(po.picking_ids.move_lines[0].stock_valuation_layer_ids), 2)

    def test_03_average(self):
        """
        Purchase twice and test the average cost is revaluated correctly
        and the standard cost is updated correctly
        """
        product_buy = self._create_product("ACG", 10, self.categ_real_time_avg)

        # I create a PO and receive it
        vendor = self.partner_model.create({"name": "Vendor"})
        po = self.create_purchase_order(vendor, product_buy, 10.0, 10.0)
        po.button_confirm()
        # Confirm and assign picking
        self._do_picking(po.picking_ids)

        # Check the value is the expected (this is still standard, just checking)
        self.assertEqual(product_buy.value_svl, 100)
        # I create a bill and a revaluation at double price the second PO only
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = vendor
        move_form.purchase_id = po
        move_form.invoice_date = fields.Datetime.now()
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 20.0
        bill = move_form.save()
        bill.action_post()

        # buy again
        po2 = self.create_purchase_order(vendor, product_buy, 10.0, 10.0)
        po2.button_confirm()
        # Confirm and assign picking
        self._do_picking(po2.picking_ids)

        # Check the value is the expected (this is still standard, just checking)
        self.assertEqual(product_buy.value_svl, 200)

        # I create a bill and a revaluation at double price the second PO only
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = vendor
        move_form.purchase_id = po2
        move_form.invoice_date = fields.Datetime.now()
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 20.0
        bill = move_form.save()
        bill.action_post()
        po2.flush()
        bill.button_revaluate()
        revaluation_ids = bill.action_view_inventory_revaluation_lines()["domain"][0][2]
        revaluation = self.revaluation_model.browse(revaluation_ids)
        revaluation.vendor_bill_id = bill
        # This will compute from the picking of the PO
        revaluation.compute_inventory_revaluation()

        # I check the revaluation lines
        reval = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_buy
        )
        self.assertEqual(reval.additional_value, 100)

        # I confirm the revaluation
        revaluation.button_validate()

        # I check the journal entry has the PO line and the value is ok
        self.assertEqual(revaluation.state, "done")
        self.assertTrue(revaluation.account_move_id)
        aml_valuation = (
            self.env["account.move.line"]
            .search([])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
                and aml.product_id == product_buy
            )
        )
        acc_value = sum(aml_valuation.mapped("balance"))
        product_value = abs(product_buy.value_svl)
        self.assertEqual(product_value, acc_value)
        self.assertEqual(
            len(po2.picking_ids.move_lines[0].stock_valuation_layer_ids), 2
        )
        # check the estandard price is (10 @ 10) + (10 @ 20) / 20 = 15
        self.assertEqual(product_buy.standard_price, 15.0)
