# Copyright 2018-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import Form, common
from odoo.tools import mute_logger


class TestAccountSpreadCostRevenue(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.sales_journal = self.env["account.journal"].create(
            {"name": "Customer Invoices - Test", "code": "TEST1", "type": "sale"}
        )

        self.expenses_journal = self.env["account.journal"].create(
            {"name": "Vendor Bills - Test", "code": "TEST2", "type": "purchase"}
        )

        type_receivable = self.env.ref("account.data_account_type_receivable")
        type_expenses = self.env.ref("account.data_account_type_expenses")
        type_payable = self.env.ref("account.data_account_type_payable")
        type_revenue = self.env.ref("account.data_account_type_revenue")

        self.credit_account = self.env["account.account"].create(
            {
                "name": "test_account_receivable",
                "code": "123",
                "user_type_id": type_receivable.id,
                "reconcile": True,
            }
        )

        self.debit_account = self.env["account.account"].create(
            {
                "name": "test account_expenses",
                "code": "765",
                "user_type_id": type_expenses.id,
                "reconcile": True,
            }
        )

        self.account_payable = self.env["account.account"].create(
            {
                "name": "test_account_payable",
                "code": "321",
                "user_type_id": type_payable.id,
                "reconcile": True,
            }
        )

        self.account_revenue = self.env["account.account"].create(
            {
                "name": "test_account_revenue",
                "code": "864",
                "user_type_id": type_revenue.id,
                "reconcile": True,
            }
        )

    def test_01_account_spread_defaults(self):
        this_year = datetime.date.today().year
        spread_template = self.env["account.spread.template"].create(
            {"name": "test", "spread_account_id": self.debit_account.id}
        )
        self.assertEqual(spread_template.spread_type, "sale")
        self.assertTrue(spread_template.spread_journal_id)

        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "out_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )

        self.assertTrue(spread)
        self.assertFalse(spread.line_ids)
        self.assertFalse(spread.invoice_line_ids)
        self.assertFalse(spread.invoice_line_id)
        self.assertFalse(spread.invoice_id)
        self.assertFalse(spread.account_analytic_id)
        self.assertFalse(spread.analytic_tag_ids)
        self.assertTrue(spread.move_line_auto_post)
        self.assertEqual(spread.name, "test")
        self.assertEqual(spread.invoice_type, "out_invoice")
        self.assertEqual(spread.company_id, self.env.company)
        self.assertEqual(spread.currency_id, self.env.company.currency_id)
        self.assertEqual(spread.period_number, 12)
        self.assertEqual(spread.period_type, "month")
        self.assertEqual(spread.debit_account_id, self.debit_account)
        self.assertEqual(spread.credit_account_id, self.credit_account)
        self.assertEqual(spread.unspread_amount, 0.0)
        self.assertEqual(spread.unposted_amount, 0.0)
        self.assertEqual(spread.total_amount, 0.0)
        self.assertEqual(spread.estimated_amount, 0.0)
        self.assertEqual(spread.spread_date, datetime.date(this_year, 1, 1))
        self.assertTrue(spread.journal_id)
        self.assertEqual(spread.journal_id.type, "general")

        self.assertFalse(spread.display_create_all_moves)
        self.assertTrue(spread.display_recompute_buttons)
        self.assertTrue(spread.display_move_line_auto_post)

    def test_02_config_defaults(self):
        self.assertFalse(self.env.company.default_spread_revenue_account_id)
        self.assertFalse(self.env.company.default_spread_expense_account_id)
        self.assertFalse(self.env.company.default_spread_revenue_journal_id)
        self.assertFalse(self.env.company.default_spread_expense_journal_id)

    @mute_logger("odoo.sql_db")
    def test_03_no_defaults(self):
        with self.assertRaises(IntegrityError):
            self.env["account.spread"].create({"name": "test"})

    @mute_logger("odoo.sql_db")
    def test_04_no_defaults(self):
        with self.assertRaises(IntegrityError):
            self.env["account.spread"].create(
                {"name": "test", "invoice_type": "out_invoice"}
            )

    def test_05_config_settings(self):
        self.env.company.default_spread_revenue_account_id = self.account_revenue
        self.env.company.default_spread_expense_account_id = self.account_payable
        self.env.company.default_spread_revenue_journal_id = self.sales_journal
        self.env.company.default_spread_expense_journal_id = self.expenses_journal

        self.assertTrue(self.env.company.default_spread_revenue_account_id)
        self.assertTrue(self.env.company.default_spread_expense_account_id)
        self.assertTrue(self.env.company.default_spread_revenue_journal_id)
        self.assertTrue(self.env.company.default_spread_expense_journal_id)

        spread_form = Form(self.env["account.spread"])
        spread_form.name = "test"
        spread_form.invoice_type = "in_invoice"
        spread_form.debit_account_id = self.debit_account
        spread_form.credit_account_id = self.credit_account
        spread = spread_form.save()

        self.assertTrue(spread)
        self.assertFalse(spread.line_ids)
        self.assertFalse(spread.invoice_line_ids)
        self.assertFalse(spread.invoice_line_id)
        self.assertFalse(spread.invoice_id)
        self.assertFalse(spread.account_analytic_id)
        self.assertFalse(spread.analytic_tag_ids)
        self.assertTrue(spread.move_line_auto_post)

        defaults = self.env["account.spread"].default_get(["company_id", "currency_id"])

        self.assertEqual(defaults["company_id"], self.env.company.id)
        self.assertEqual(defaults["currency_id"], self.env.company.currency_id.id)

        spread_form = Form(spread)
        spread_form.invoice_type = "out_invoice"
        spread_form.company_id = self.env.company
        spread = spread_form.save()
        self.assertEqual(spread.debit_account_id, self.account_revenue)
        self.assertFalse(spread.is_debit_account_deprecated)
        self.assertEqual(spread.journal_id, self.sales_journal)
        self.assertEqual(spread.spread_type, "sale")

        spread_form = Form(spread)
        spread_form.invoice_type = "in_invoice"
        spread = spread_form.save()
        self.assertEqual(spread.credit_account_id, self.account_payable)
        self.assertFalse(spread.is_credit_account_deprecated)
        self.assertEqual(spread.journal_id, self.expenses_journal)
        self.assertEqual(spread.spread_type, "purchase")

    def test_07_create_spread_template(self):
        spread_template = self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "sale",
                "spread_account_id": self.account_revenue.id,
            }
        )

        self.assertEqual(spread_template.company_id, self.env.company)
        self.assertTrue(spread_template.spread_journal_id)

        self.env.company.default_spread_revenue_account_id = self.account_revenue
        self.env.company.default_spread_expense_account_id = self.account_payable
        self.env.company.default_spread_revenue_journal_id = self.sales_journal
        self.env.company.default_spread_expense_journal_id = self.expenses_journal

        spread_template.spread_type = "purchase"
        self.assertTrue(spread_template.spread_journal_id)
        self.assertTrue(spread_template.spread_account_id)
        self.assertEqual(spread_template.spread_account_id, self.account_payable)
        self.assertEqual(spread_template.spread_journal_id, self.expenses_journal)

        spread_vals = spread_template._prepare_spread_from_template()
        self.assertTrue(spread_vals["name"])
        self.assertTrue(spread_vals["template_id"])
        self.assertTrue(spread_vals["journal_id"])
        self.assertTrue(spread_vals["company_id"])
        self.assertTrue(spread_vals["invoice_type"])
        self.assertTrue(spread_vals["credit_account_id"])

        spread_template.spread_type = "sale"
        self.assertTrue(spread_template.spread_journal_id)
        self.assertTrue(spread_template.spread_account_id)
        self.assertEqual(spread_template.spread_account_id, self.account_revenue)
        self.assertEqual(spread_template.spread_journal_id, self.sales_journal)

        spread_vals = spread_template._prepare_spread_from_template()
        self.assertTrue(spread_vals["name"])
        self.assertTrue(spread_vals["template_id"])
        self.assertTrue(spread_vals["journal_id"])
        self.assertTrue(spread_vals["company_id"])
        self.assertTrue(spread_vals["invoice_type"])
        self.assertTrue(spread_vals["debit_account_id"])

    def test_08_check_template_invoice_type(self):
        template_sale = self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "sale",
                "spread_account_id": self.account_revenue.id,
            }
        )
        template_purchase = self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "purchase",
                "spread_account_id": self.account_payable.id,
            }
        )
        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "out_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )

        with self.assertRaises(ValidationError):
            spread.template_id = template_purchase

        spread.template_id = template_sale
        self.assertEqual(spread.template_id, template_sale)

        self.assertFalse(spread.display_create_all_moves)
        self.assertTrue(spread.display_recompute_buttons)
        self.assertTrue(spread.display_move_line_auto_post)

        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "in_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )

        with self.assertRaises(ValidationError):
            spread.template_id = template_sale

        spread.template_id = template_purchase
        self.assertEqual(spread.template_id, template_purchase)

        self.assertFalse(spread.display_create_all_moves)
        self.assertTrue(spread.display_recompute_buttons)
        self.assertTrue(spread.display_move_line_auto_post)

    def test_10_account_spread_unlink(self):
        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "out_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )
        spread.unlink()

    def test_11_compute_display_fields(self):
        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "out_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )
        spread.company_id.allow_spread_planning = True
        self.assertFalse(spread.display_create_all_moves)
        self.assertTrue(spread.display_recompute_buttons)
        self.assertTrue(spread.display_move_line_auto_post)

    def test_12_compute_display_fields(self):
        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "out_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )
        spread.company_id.allow_spread_planning = False
        self.assertFalse(spread.display_create_all_moves)
        self.assertTrue(spread.display_recompute_buttons)
        self.assertTrue(spread.display_move_line_auto_post)

    def test_13_compute_display_fields(self):
        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "out_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )
        spread.company_id.force_move_auto_post = True
        self.assertFalse(spread.display_create_all_moves)
        self.assertTrue(spread.display_recompute_buttons)
        self.assertFalse(spread.display_move_line_auto_post)

    def test_14_compute_display_fields(self):
        spread = self.env["account.spread"].create(
            {
                "name": "test",
                "invoice_type": "out_invoice",
                "debit_account_id": self.debit_account.id,
                "credit_account_id": self.credit_account.id,
            }
        )
        spread.company_id.force_move_auto_post = False
        self.assertFalse(spread.display_create_all_moves)
        self.assertTrue(spread.display_recompute_buttons)
        self.assertTrue(spread.display_move_line_auto_post)
