# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.stock_account.tests.test_anglo_saxon_valuation_reconciliation_common import (  # noqa: E501
    ValuationReconciliationTestCommon,
)


@tagged("post_install", "-at_install")
class TestAccountMoveLineRepairInfoSale(ValuationReconciliationTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.anglo_saxon_accounting = True
        cls.part = cls.env["product.product"].create(
            {
                "name": "Spare Bearing",
                "is_storable": True,
                "categ_id": cls.stock_account_product_categ.id,
                "standard_price": 10.0,
                "taxes_id": False,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.part, cls.company_data["default_warehouse"].lot_stock_id, 5
        )

    @classmethod
    def _create_invoice_from_repair(cls):
        repair = cls.env["repair.order"].create(
            {
                "product_id": cls.product_a.id,
                "partner_id": cls.partner_a.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "repair_line_type": "add",
                            "product_id": cls.part.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()
        repair.sudo().action_create_sale_order()
        sale_order = repair.sale_order_id
        sale_order.sudo().action_confirm()
        invoice = sale_order._create_invoices()
        invoice.action_post()
        return repair, invoice

    def test_repair_order_on_invoice_lines(self):
        repair, invoice = self._create_invoice_from_repair()
        self.assertEqual(invoice.invoice_line_ids.mapped("repair_order_id"), repair)

    def test_repair_order_on_cogs_lines(self):
        repair, invoice = self._create_invoice_from_repair()
        cogs_lines = invoice.line_ids.filtered(lambda line: line.display_type == "cogs")
        self.assertTrue(cogs_lines)
        self.assertEqual(cogs_lines.mapped("repair_order_id"), repair)
