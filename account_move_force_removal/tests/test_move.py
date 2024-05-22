# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMove(TransactionCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.env = self.env(
            context=dict(
                self.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        self.partner = self.env["res.partner"].create(
            {"name": "Test customer", "customer_rank": 1}
        )
        self.journal = self.env["account.journal"].create(
            {
                "name": "Test journal",
                "type": "sale",
                "code": "test-sale-jorunal",
                "company_id": self.env.company.id,
            }
        )
        self.product = self.env["product.product"].create(
            {"name": "Test product", "type": "service"}
        )
        self.company = self.env.company
        self.company.currency_id.active = True
        self.income_account = self.env["account.account"].search(
            [
                ("account_type", "=", "income"),
                ("company_id", "=", self.company.id),
            ],
            limit=1,
        )

        invoice = Form(
            self.env["account.move"].with_context(
                default_type="out_invoice",
                default_company_id=self.env.company.id,
            ),
            self.env.ref("account.view_move_form"),
        )
        # invoice.save()
        invoice.partner_id = self.partner
        invoice.journal_id = self.journal
        with invoice.invoice_line_ids.new() as line_form:
            line_form.name = self.product.name
            line_form.product_id = self.product.id
            line_form.quantity = 1.0
            line_form.price_unit = 10
            line_form.account_id = self.income_account
        invoice = invoice.save()
        invoice.action_post()
        self.invoice = invoice
        self.invoice2 = self.invoice.copy()
        self.invoice2.action_post()
        self.invoice3 = self.invoice.copy()
        self.invoice3.action_post()

    def test_remove_invoice_error(self):
        # Delete invoice while name isn't / and
        # user not in group_account_move_force_removal
        with self.assertRaises(UserError):
            self.invoice.unlink()
        # Delete invoice (previously draft + cancel) and
        # user not in group_account_move_force_removal
        self.invoice.button_draft()
        self.invoice.button_cancel()
        with self.assertRaises(UserError):
            self.invoice.unlink()
        # Delete invoice while name isn't / and
        # user in group_account_move_force_removal
        self.env.user.groups_id += self.env.ref(
            "account_move_force_removal.group_account_move_force_removal"
        )
        with self.assertRaises(UserError):
            self.invoice3.unlink()

    def test_ok_invoice_error(self):
        # Delete invoice (previously draft + cancel) and
        # user in group_account_move_force_removal
        self.invoice.button_draft()
        self.invoice.button_cancel()
        self.env.user.groups_id += self.env.ref(
            "account_move_force_removal.group_account_move_force_removal"
        )
        self.invoice.unlink()
