# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.stock_inventory_revaluation.tests.common import (
    TestStockInventoryRevaluationCommon,
)


@tagged("post_install", "-at_install")
class TestStockInventoryRevaluationDropshipping(TestStockInventoryRevaluationCommon):
    def test_01_stock_inventory_revaluation_dropshipping(self):
        """
        Revaluate an dropship and check the layer values and journal entries
        """
        product_drop = self._create_product("FIFO", 10, self.categ_real_time_fifo)
        # enable the dropship and MTO route on the product
        dropshipping_route = self.env.ref("stock_dropshipping.route_drop_shipping")
        mto_route = self.env.ref("stock.route_warehouse0_mto")
        product_drop.write(
            {"route_ids": [(6, 0, [dropshipping_route.id, mto_route.id])]}
        )
        # add a vendor
        vendor1 = self.env["res.partner"].create({"name": "vendor1"})
        seller1 = self.env["product.supplierinfo"].create(
            {
                "name": vendor1.id,
                "price": 10,
            }
        )
        product_drop.write({"seller_ids": [(6, 0, [seller1.id])]})
        # sell one unit of this product
        customer1 = self.env["res.partner"].create({"name": "customer1"})
        so = self.env["sale.order"].create(
            {
                "partner_id": customer1.id,
                "partner_invoice_id": customer1.id,
                "partner_shipping_id": customer1.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": product_drop.name,
                            "product_id": product_drop.id,
                            "product_uom_qty": 10,
                            "product_uom": product_drop.uom_id.id,
                            "price_unit": 20,
                            "tax_id": [(6, 0, [])],
                        },
                    )
                ],
                "pricelist_id": self.env.ref("product.list0").id,
                "picking_policy": "direct",
            }
        )
        so.action_confirm()
        # confirm the purchase order
        po = self.env["purchase.order"].search(
            [("group_id", "=", so.procurement_group_id.id)]
        )
        po.button_confirm()
        # validate the dropshipping picking
        self.assertEqual(len(so.picking_ids), 1)
        wizard = so.picking_ids.button_validate()
        immediate_transfer = Form(
            self.env[wizard["res_model"]].with_context(wizard["context"])
        ).save()
        immediate_transfer.process()
        self.assertEqual(so.picking_ids.state, "done")
        # do the customer invoice, it can be done later without affecting the revalaution
        so._create_invoices()
        so.invoice_ids.action_post()
        # I create a bill and a revaluation at double price
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = vendor1
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
        # This will compute from the picking of the dropship
        revaluation.compute_inventory_revaluation()

        # I check the revaluation lines
        reval = revaluation.stock_inventory_revaluation_line_ids.filtered(
            lambda l: l.product_id == product_drop
        )
        self.assertEqual(reval.additional_value, 100)

        # I confirm the revaluation
        revaluation.button_validate()

        # I check the journal entry valuation
        self.assertEqual(revaluation.state, "done")
        self.assertTrue(revaluation.account_move_id)
        aml_valuation = (
            self.env["account.move.line"]
            .search([])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_valuation"]
                and aml.product_id == product_drop
            )
        )
        acc_value = sum(aml_valuation.mapped("balance"))
        product_value = abs(product_drop.value_svl)
        # Check the value and the number of layers
        self.assertEqual(product_value, acc_value)
        self.assertEqual(len(po.picking_ids.move_lines[0].stock_valuation_layer_ids), 4)
        self.assertEqual(
            len(
                revaluation.mapped(
                    "stock_inventory_revaluation_line_ids.used_stock_valuation_layer_ids"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                revaluation.mapped(
                    "stock_inventory_revaluation_line_ids.created_stock_valuation_layer_ids"
                )
            ),
            2,
        )
        # Check the interim input
        aml_stock_input = (
            self.env["account.move.line"]
            .search([])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_in"]
                and aml.product_id == product_drop
            )
        )
        open_input = sum(aml_stock_input.mapped("balance"))
        self.assertEqual(open_input, 0.0)
        # Check the interim output
        aml_stock_output = (
            self.env["account.move.line"]
            .search([])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_out"]
                and aml.product_id == product_drop
            )
        )
        open_output = sum(aml_stock_output.mapped("balance"))
        self.assertEqual(open_output, 0.0)
        # Check the expenses, with are 10 units @ 20
        aml_stock_expense = (
            self.env["account.move.line"]
            .search([])
            .filtered(
                lambda aml: aml.account_id
                == self.company_data["default_account_stock_expense"]
                and aml.product_id == product_drop
            )
        )
        open_expense = sum(aml_stock_expense.mapped("balance"))
        self.assertEqual(open_expense, 200.0)
