# Copyright 2017-2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountCostCenter(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.expenses_account = cls.env["account.account"].create(
            {
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )

        cls.costcenter = cls.env["account.cost.center"].create(
            {
                "name": "Cost Center Test",
                "code": "CC1",
                "company_id": cls.env.company.id,
            }
        )

        # Invoice created with tests Form
        cls.invoice1 = cls.init_invoice("in_invoice")

        # Invoice created with standard create
        cls.invoice2 = (
            cls.env["account.move"]
            .with_context(cost_center_id=cls.costcenter.id)
            .create(
                {
                    "partner_id": cls.env.ref("base.res_partner_2").id,
                    "move_type": "in_invoice",
                    "cost_center_id": cls.costcenter.id,
                }
            )
        )

        cls.invoice2.invoice_line_ids += cls.env["account.move.line"].new(
            {
                "product_id": cls.env.ref("product.product_product_4").id,
                "quantity": 1.0,
                "price_unit": 130.0,
                "name": "product that cost 130",
                "cost_center_id": cls.costcenter.id,
            }
        )

    def test_01_check_lines(self):
        self.assertFalse(
            self.invoice1.invoice_line_ids.cost_center_id,
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
        self.assertFalse(any(line.cost_center_id for line in invoice_lines))
        self.assertTrue(any(not line.cost_center_id for line in invoice_lines))

    def test_03_confirm_invoice(self):
        invoice_lines = self.invoice2.invoice_line_ids
        for move_line in invoice_lines:
            self.assertEqual(move_line.cost_center_id, self.costcenter)
        for move_line in self.invoice2.line_ids - invoice_lines:
            self.assertFalse(move_line.cost_center_id)

    def test_04_search_read(self):
        expected_cost_center = self.costcenter

        records = self.env["account.invoice.report"].sudo().search_read([])
        result = records[0].get("cost_center_id")

        self.assertTrue(result)
        self.assertEqual(result[0], expected_cost_center.id)
        self.assertEqual(result[1], expected_cost_center.name)
