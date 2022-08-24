# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import Form, tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class TestAccount(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_account_type_model = cls.env["account.account.type"]
        cls.account_account_model = cls.env["account.account"]
        cls.account_type_regular = cls.account_account_type_model.create(
            {"name": "Test Regular", "type": "other", "internal_group": "income"}
        )
        cls.account_income = cls.account_account_model.create(
            {
                "name": "Test Income",
                "code": "TEST_IN",
                "user_type_id": cls.account_type_regular.id,
                "reconcile": False,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "service"}
        )
        invoice = Form(
            cls.env["account.move"].with_context(
                default_type="out_invoice", default_company_id=cls.env.company.id
            )
        )
        invoice.partner_id = cls.partner
        with invoice.invoice_line_ids.new() as line_form:
            line_form.name = cls.product.name
            line_form.product_id = cls.product
            line_form.quantity = 1.0
            line_form.price_unit = 10
            line_form.account_id = cls.account_income
        with invoice.invoice_line_ids.new() as line_form:
            line_form.name = cls.product.name
            line_form.product_id = cls.product
            line_form.quantity = 2.0
            line_form.price_unit = 10
            line_form.account_id = cls.account_income
        invoice = invoice.save()
        invoice.action_post()
        cls.invoice = invoice

    def test_basic_check(self):
        lines = (
            self.env["account.move.line"]
            .with_context(domain_cumulated_balance=[("parent_state", "=", "posted")])
            .search(
                [
                    ("account_id", "=", self.account_income.id),
                    ("move_id", "=", self.invoice.id),
                ],
                order="date asc, id asc",
            )
        )
        self.assertAlmostEqual(lines[0].cumulated_balance, -10)
        # TODO: Test other currency balances
        self.assertAlmostEqual(lines[0].cumulated_balance_currency, 0)
        self.assertAlmostEqual(lines[1].cumulated_balance, -30)
        self.assertAlmostEqual(lines[1].cumulated_balance_currency, 0)
