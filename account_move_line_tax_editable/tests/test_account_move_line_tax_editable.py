# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveLineTaxEditable(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        refund_repartitions = cls.company_data[
            "default_tax_sale"
        ].refund_repartition_line_ids
        tax_repartition_line = refund_repartitions.filtered(
            lambda line: line.repartition_type == "tax"
        )
        cls.account_revenue = cls.company_data["default_account_revenue"]
        cls.account_expense = cls.company_data["default_account_expense"]
        cls.account_tax_sale = cls.company_data["default_account_tax_sale"]
        cls.tax_sale = cls.company_data["default_tax_sale"]
        cls.tax_sale_copy = cls.tax_sale.copy({"name": "Test sale tax"})
        cls.test_move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2016-01-01"),
                "line_ids": [
                    (
                        0,
                        None,
                        {
                            "name": "revenue line 1",
                            "account_id": cls.account_revenue.id,
                            "debit": 500.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        None,
                        {
                            "name": "revenue line 2",
                            "account_id": cls.account_revenue.id,
                            "debit": 1000.0,
                            "credit": 0.0,
                            "tax_ids": [(6, 0, cls.tax_sale.ids)],
                        },
                    ),
                    (
                        0,
                        None,
                        {
                            "name": "tax line",
                            "account_id": cls.account_tax_sale.id,
                            "debit": 150.0,
                            "credit": 0.0,
                            "tax_repartition_line_id": tax_repartition_line.id,
                        },
                    ),
                    (
                        0,
                        None,
                        {
                            "name": "counterpart line",
                            "account_id": cls.account_expense.id,
                            "debit": 0.0,
                            "credit": 1650.0,
                        },
                    ),
                ],
            }
        )

    def test_compute_is_tax_editable(self):
        self.assertTrue(all(self.test_move.line_ids.mapped("is_tax_editable")))
        self.test_move.action_post()
        self.assertFalse(any(self.test_move.line_ids.mapped("is_tax_editable")))

    def test_tax_edited(self):
        tax_line = self.test_move.line_ids.filtered(
            lambda x: x.account_id == self.account_tax_sale
        )
        self.assertEqual(tax_line.tax_repartition_line_id.tax_id, self.tax_sale)
        self.assertEqual(tax_line.tax_line_id, self.tax_sale)
        tax_line.tax_line_id = self.tax_sale_copy.id
        self.test_move.action_post()
        self.assertEqual(tax_line.tax_line_id.id, self.tax_sale_copy.id)
        self.assertEqual(
            tax_line.tax_repartition_line_id.tax_id.id, self.tax_sale_copy.id
        )

    def test_tax_not_edited(self):
        """In this case we set the tax_repartition_line_id field, simulating that the
        move came from an invoice with tax applied. Thus, tax_line_id should be computed"""
        tax_line = self.test_move.line_ids.filtered(
            lambda x: x.account_id == self.account_tax_sale
        )
        tax_line.tax_line_id = self.tax_sale_copy.id
        tax_line.tax_repartition_line_id = (
            self.tax_sale_copy.invoice_repartition_line_ids[1]
        )
        self.assertEqual(tax_line.tax_line_id.id, self.tax_sale_copy.id)
