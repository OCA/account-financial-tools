# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime

from odoo import fields
from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class StockAccountNoAutoReconcile(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_obj = cls.env["product.product"]
        cls.category_obj = cls.env["product.category"]
        cls.partner_obj = cls.env["res.partner"]
        cls.po_obj = cls.env["purchase.order"]
        cls.acc_obj = cls.env["account.account"]
        cls.categ_unit = cls.env.ref("uom.product_uom_categ_unit")
        assets = cls.env.ref("account.data_account_type_current_assets")
        expenses = cls.env.ref("account.data_account_type_expenses")
        equity = cls.env.ref("account.data_account_type_equity")
        cls.company = cls.env.ref("base.main_company")

        # Create partner:
        cls.partner = cls.partner_obj.create({"name": "Test Vendor"})
        # Create standard product:
        cls.product = cls.product_obj.create(
            {"name": "saled Product", "type": "product"}
        )
        # Create product that uses a reconcilable stock input account.
        cls.stock_journal = cls.env["account.journal"].create(
            {"name": "Stock Journal", "code": "STJTEST", "type": "general"}
        )
        cls.sale_journal = cls.env["account.journal"].create(
            {"name": "Sales Journal", "code": "SLTEST", "type": "sale"}
        )
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        acc_type = equity
        cls.account_grni = cls._create_account(
            acc_type, name, code, cls.company, reconcile=True
        )
        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        acc_type = expenses
        cls.account_cogs = cls._create_account(acc_type, name, code, cls.company)
        # Create account for Goods Delivered Not Invoiced
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        acc_type = expenses
        cls.account_gdni = cls._create_account(
            acc_type, name, code, cls.company, reconcile=True
        )
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        acc_type = assets
        cls.account_inventory = cls._create_account(acc_type, name, code, cls.company)
        cls.product_categ = cls.category_obj.create(
            {
                "name": "Test Category",
                "property_cost_method": "standard",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_stock_account_input_categ_id": cls.account_grni.id,
                "property_account_expense_categ_id": cls.account_cogs.id,
                "property_stock_account_output_categ_id": cls.account_gdni.id,
                "property_valuation": "real_time",
                "property_stock_journal": cls.stock_journal.id,
            }
        )
        cls.product_to_reconcile = cls.product_obj.create(
            {
                "name": "Purchased Product (To reconcile)",
                "type": "product",
                "standard_price": 100.0,
                "categ_id": cls.product_categ.id,
            }
        )

    @classmethod
    def _create_account(cls, acc_type, name, code, company, reconcile=False):
        """Create an account."""
        account = cls.acc_obj.create(
            {
                "name": name,
                "code": code,
                "user_type_id": acc_type.id,
                "company_id": company.id,
                "reconcile": reconcile,
            }
        )
        return account

    def _do_picking(self, picking, date):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        picking.move_lines.quantity_done = picking.move_lines.product_uom_qty
        picking._action_done()
        for move in picking.move_lines:
            move.date = date

    def test_01_no_reconcile_interim(self):
        """Tests the case into which we receive the goods first, and then make the invoice."""
        self.company.anglo_saxon_auto_reconcile = False
        po = self.po_obj.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_to_reconcile.id,
                            "name": self.product_to_reconcile.name,
                            "product_qty": 5.0,
                            "price_unit": 100.0,
                            "product_uom": self.product_to_reconcile.uom_id.id,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        po.button_confirm()
        self._do_picking(po.picking_ids, fields.Datetime.now())
        # Invoice created and validated:
        po.action_create_invoice()
        invoice_ids = po.invoice_ids.filtered(lambda i: i.move_type == "in_invoice")
        invoice_ids.invoice_date = datetime.now()
        invoice_ids.action_post()
        # should not be reconciled
        stock_moves = po.picking_ids.move_lines
        interim_account_id = self.account_grni.id
        valuation_line = stock_moves.mapped("account_move_ids.line_ids").filtered(
            lambda x: x.account_id.id == interim_account_id
        )
        self.assertFalse(valuation_line.reconciled)
