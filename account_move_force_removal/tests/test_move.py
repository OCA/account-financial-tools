# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import SavepointCase


class TestMove(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test customer", "customer_rank": 1}
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test journal",
                "type": "sale",
                "code": "test-sale-jorunal",
                "company_id": cls.env.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "service"}
        )
        cls.company = cls.env.company
        account_type = cls.env.ref("account.data_account_type_other_income")
        cls.income_account = cls.env["account.account"].search(
            [
                ("user_type_id", "=", account_type.id),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )

        invoice = Form(
            cls.env["account.move"].with_context(
                default_type="out_invoice", default_company_id=cls.env.company.id
            )
        )
        invoice.partner_id = cls.partner
        invoice.journal_id = cls.journal
        with invoice.invoice_line_ids.new() as line_form:
            line_form.name = cls.product.name
            line_form.product_id = cls.product
            line_form.quantity = 1.0
            line_form.price_unit = 10
            line_form.account_id = cls.income_account
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
