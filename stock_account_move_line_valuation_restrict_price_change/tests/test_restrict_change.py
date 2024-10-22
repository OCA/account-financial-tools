# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import Form, users

from odoo.addons.base.tests.common import BaseCommon


class TestAccountMoveDraft(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_obj = cls.env["stock.picking"]
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.suppliers = cls.env.ref("stock.stock_location_suppliers")
        cls.stock = cls.env.ref("stock.stock_location_stock")
        cls.account_group = cls.env.ref("account.group_account_user")
        cls.stock_manager = cls.env.ref("stock.group_stock_manager")
        cls.account_model = cls.env["account.account"]
        cls.user_account = cls.env["res.users"].create(
            {
                "name": "Account User",
                "login": "test-account-user-draft",
                "email": "test@test.com",
                "groups_id": [Command.set((cls.account_group | cls.stock_manager).ids)],
            }
        )
        cls.inventory_account = cls.account_model.create(
            {
                "name": "Inventory variations",
                "code": "INV",
                "account_type": "expense",
                "reconcile": True,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "type": "product",
                "standard_price": 5.0,
            }
        )
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Test Supplier",
            }
        )
        cls.env.company.restrict_account_move_line_change_after_valuation = True

    def _create_picking(self):
        self.picking = self.picking_obj.create(
            {
                "partner_id": self.supplier.id,
                "picking_type_id": self.picking_type_in.id,
                "location_id": self.suppliers.id,
                "location_dest_id": self.stock.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "location_id": self.suppliers.id,
                            "location_dest_id": self.stock.id,
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "product_uom_qty": 5.0,
                        }
                    )
                ],
            }
        )
        self.picking.action_confirm()

    def _create_in_invoice(self):
        # Create manually the invoice to mimic what should happen in purchase
        with Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        ) as invoice_form:
            invoice_form.partner_id = self.partner
            invoice_form.invoice_date = "2024-01-01"
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
                line_form.quantity = 5.0

        self.invoice = invoice_form.save()
        self.invoice._post()

    def _create_valuation_line(self):
        move = self.picking.move_ids
        self.layer = self.env["stock.valuation.layer"].create(
            {
                "stock_valuation_layer_id": move.stock_valuation_layer_ids.id,
                "product_id": move.product_id.id,
                "quantity": 0.0,
                "value": self.invoice.invoice_line_ids.amount_currency,
                "account_move_line_id": self.invoice.invoice_line_ids.id,
                "company_id": self.invoice.company_id.id,
            }
        )

    @users("test-account-user-draft")
    def test_action_draft(self):
        self._create_picking()
        self.picking.move_line_ids.qty_done = 5.0
        self.picking._action_done()
        self._create_in_invoice()

        # Create the valuation line
        self._create_valuation_line()

        self.invoice.button_draft()

        with self.assertRaises(UserError) as error:
            self.invoice.invoice_line_ids.price_unit = 15.0

        self.assertIn(
            "You cannot change the price of the accounting entry",
            error.exception.args[0],
        )

        self.env.company.sudo().restrict_account_move_line_change_after_valuation = (
            False
        )
        self.invoice.invoice_line_ids.price_unit = 15.0
