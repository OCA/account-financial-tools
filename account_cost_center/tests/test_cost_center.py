# Copyright 2017-2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.account.tests.account_test_savepoint import AccountTestInvoicingCommon


class TestAccountCostCenter(AccountTestInvoicingCommon):
    def setUp(self):
        super().setUp()

        self.expenses_account = self.env["account.account"].create(
            {
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )

        self.costcenter = self.env["account.cost.center"].create(
            {
                "name": "Cost Center Test",
                "code": "CC1",
                "company_id": self.env.company.id,
            }
        )

        # Invoice created with tests Form
        self.invoice1 = self.init_invoice("in_invoice")

        # Invoice created with standard create
        self.invoice2 = (
            self.env["account.move"]
            .with_context(cost_center_id=self.costcenter.id)
            .create(
                {
                    "partner_id": self.env.ref("base.res_partner_2").id,
                    "type": "in_invoice",
                    "cost_center_id": self.costcenter.id,
                }
            )
        )

        self.invoice2.invoice_line_ids += self.env["account.move.line"].new(
            {
                "product_id": self.env.ref("product.product_product_4").id,
                "quantity": 1.0,
                "price_unit": 130.0,
                "name": "product that cost 130",
                "cost_center_id": self.costcenter.id,
            }
        )

    def test_01_check_lines(self):
        self.assertFalse(
            self.invoice1.invoice_line_ids[0].cost_center_id,
            "Default cost center per line not set",
        )

        self.assertEqual(
            self.invoice2.invoice_line_ids[0].cost_center_id, self.costcenter
        )

    def test_02_check_lines(self):
        invoice_lines = self.invoice1.invoice_line_ids
        self.assertFalse(any(line.cost_center_id for line in invoice_lines))

        invoice_form = Form(self.invoice1)
        invoice_form.cost_center_id = self.costcenter
        with invoice_form.invoice_line_ids.new() as line:
            line.name = "Test line2"
            line.quantity = 2.0
            line.price_unit = 200.0
            line.account_id = self.expenses_account
        self.invoice1 = invoice_form.save()

        invoice_lines = self.invoice1.invoice_line_ids
        self.assertTrue(any(line.cost_center_id for line in invoice_lines))
        self.assertTrue(any(not line.cost_center_id for line in invoice_lines))

    def test_03_confirm_invoice(self):
        invoice_lines = self.invoice2.invoice_line_ids
        for move_line in invoice_lines:
            self.assertEqual(move_line.cost_center_id, self.costcenter)
        for move_line in self.invoice2.line_ids - invoice_lines:
            self.assertFalse(move_line.cost_center_id)
