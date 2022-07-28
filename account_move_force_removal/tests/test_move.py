# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class TestMove(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test customer", "customer_rank": 1}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "service"}
        )
        cls.company = cls.env.company
        invoice = Form(
            cls.env["account.move"].with_context(
                default_move_type="out_invoice", default_company_id=cls.env.company.id
            )
        )
        invoice.partner_id = cls.partner
        with invoice.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product
            line_form.quantity = 1.0
            line_form.price_unit = 10
        invoice = invoice.save()
        invoice.action_post()
        cls.invoice = invoice

    def test_remove_invoice_error(self):
        # Delete invoice while name isn't /
        with self.assertRaises(UserError):
            self.invoice.unlink()

    def test_ok_invoice_error(self):
        # Delete invoice (previously draft + camcel)
        self.invoice.button_draft()
        self.invoice.button_cancel()
        self.invoice.unlink()
