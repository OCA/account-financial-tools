# Copyright 2018-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_resource_path
from odoo.tests import Form, common
from odoo.tools import convert_file


class TestAccountInvoiceSpread(common.TransactionCase):
    def _load(self, module, *args):
        convert_file(
            self.cr,
            "account_spread_cost_revenue",
            get_resource_path(module, *args),
            {},
            "init",
            False,
            "test",
            self.registry._assertion_report,
        )

    def create_account_invoice(self, invoice_type, quantity=1.0, price_unit=1000.0):
        """ Create an invoice as in a view by triggering its onchange methods"""

        invoice_form = Form(
            self.env["account.move"].with_context(default_type=invoice_type)
        )
        invoice_form.partner_id = self.env["res.partner"].create(
            {"name": "Partner Name"}
        )
        with invoice_form.invoice_line_ids.new() as line:
            line.name = "product that costs " + str(price_unit)
            line.quantity = quantity
            line.price_unit = price_unit

        return invoice_form.save()

    def setUp(self):
        super().setUp()
        self._load("account", "test", "account_minimal_test.xml")

        self.account_payable = self.env["account.account"].create(
            {
                "name": "Test account payable",
                "code": "321spread",
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
                "reconcile": True,
            }
        )

        self.account_receivable = self.env["account.account"].create(
            {
                "name": "Test account receivable",
                "code": "322spread",
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
                "reconcile": True,
            }
        )

        spread_account_payable = self.env["account.account"].create(
            {
                "name": "test spread account_payable",
                "code": "765spread",
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
                "reconcile": True,
            }
        )

        spread_account_receivable = self.env["account.account"].create(
            {
                "name": "test spread account_receivable",
                "code": "766spread",
                "user_type_id": self.env.ref(
                    "account.data_account_type_other_income"
                ).id,
                "reconcile": True,
            }
        )

        # Invoices
        self.vendor_bill = self.create_account_invoice("in_invoice")
        self.sale_invoice = self.create_account_invoice("out_invoice")
        self.vendor_bill_line = self.vendor_bill.invoice_line_ids[0]
        self.invoice_line = self.sale_invoice.invoice_line_ids[0]

        # Set accounts to reconcilable
        self.vendor_bill_line.account_id.reconcile = True
        self.invoice_line.account_id.reconcile = True

        analytic_tags = [(6, 0, self.env.ref("analytic.tag_contract").ids)]
        self.analytic_account = self.env["account.analytic.account"].create(
            {"name": "test account"}
        )
        self.spread = (
            self.env["account.spread"]
            .with_context(mail_create_nosubscribe=True)
            .create(
                [
                    {
                        "name": "test",
                        "debit_account_id": spread_account_payable.id,
                        "credit_account_id": self.account_payable.id,
                        "period_number": 12,
                        "period_type": "month",
                        "spread_date": datetime.date(2017, 2, 1),
                        "estimated_amount": 1000.0,
                        "journal_id": self.vendor_bill.journal_id.id,
                        "invoice_type": "in_invoice",
                        "account_analytic_id": self.analytic_account.id,
                        "analytic_tag_ids": analytic_tags,
                    }
                ]
            )
        )

        self.spread2 = self.env["account.spread"].create(
            [
                {
                    "name": "test2",
                    "debit_account_id": spread_account_receivable.id,
                    "credit_account_id": self.account_receivable.id,
                    "period_number": 12,
                    "period_type": "month",
                    "spread_date": datetime.date(2017, 2, 1),
                    "estimated_amount": 1000.0,
                    "journal_id": self.sale_invoice.journal_id.id,
                    "invoice_type": "out_invoice",
                }
            ]
        )

    def test_01_wizard_defaults(self):
        Wizard = self.env["account.spread.invoice.line.link.wizard"]

        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.vendor_bill_line.id,
            default_company_id=self.env.company.id,
            allow_spread_planning=True,
        ).create({})

        self.assertEqual(wizard1.invoice_line_id, self.vendor_bill_line)
        self.assertEqual(wizard1.invoice_line_id.move_id, self.vendor_bill)
        self.assertEqual(wizard1.invoice_type, "in_invoice")
        self.assertFalse(wizard1.spread_id)
        self.assertEqual(wizard1.company_id, self.env.company)
        self.assertEqual(wizard1.spread_action_type, "link")
        self.assertFalse(wizard1.spread_account_id)
        self.assertFalse(wizard1.spread_journal_id)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=self.env.company.id,
        ).create({})

        self.assertEqual(wizard2.invoice_line_id, self.invoice_line)
        self.assertEqual(wizard2.invoice_line_id.move_id, self.sale_invoice)
        self.assertEqual(wizard2.invoice_type, "out_invoice")
        self.assertFalse(wizard2.spread_id)
        self.assertEqual(wizard2.company_id, self.env.company)
        self.assertEqual(wizard2.spread_action_type, "template")
        self.assertFalse(wizard2.spread_account_id)
        self.assertFalse(wizard2.spread_journal_id)

    def test_02_wizard_defaults(self):
        Wizard = self.env["account.spread.invoice.line.link.wizard"]

        exp_journal = self.ref("account_spread_cost_revenue.expenses_journal")
        sales_journal = self.ref("account_spread_cost_revenue.sales_journal")
        self.env.company.default_spread_revenue_account_id = self.account_receivable
        self.env.company.default_spread_expense_account_id = self.account_payable
        self.env.company.default_spread_revenue_journal_id = sales_journal
        self.env.company.default_spread_expense_journal_id = exp_journal

        self.assertTrue(self.env.company.default_spread_revenue_account_id)
        self.assertTrue(self.env.company.default_spread_expense_account_id)
        self.assertTrue(self.env.company.default_spread_revenue_journal_id)
        self.assertTrue(self.env.company.default_spread_expense_journal_id)

        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.vendor_bill_line.id,
            default_company_id=self.env.company.id,
            allow_spread_planning=True,
        ).create({})

        self.assertEqual(wizard1.invoice_line_id, self.vendor_bill_line)
        self.assertEqual(wizard1.invoice_line_id.move_id, self.vendor_bill)
        self.assertEqual(wizard1.invoice_type, "in_invoice")
        self.assertFalse(wizard1.spread_id)
        self.assertEqual(wizard1.company_id, self.env.company)
        self.assertEqual(wizard1.spread_action_type, "link")
        self.assertTrue(wizard1.spread_account_id)
        self.assertTrue(wizard1.spread_journal_id)
        self.assertEqual(wizard1.spread_account_id, self.account_payable)
        self.assertEqual(wizard1.spread_journal_id.id, exp_journal)
        self.assertTrue(wizard1.spread_invoice_type_domain_ids)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=self.env.company.id,
        ).create({})

        self.assertEqual(wizard2.invoice_line_id, self.invoice_line)
        self.assertEqual(wizard2.invoice_line_id.move_id, self.sale_invoice)
        self.assertEqual(wizard2.invoice_type, "out_invoice")
        self.assertFalse(wizard2.spread_id)
        self.assertEqual(wizard2.company_id, self.env.company)
        self.assertEqual(wizard2.spread_action_type, "template")
        self.assertTrue(wizard2.spread_account_id)
        self.assertTrue(wizard2.spread_journal_id)
        self.assertEqual(wizard2.spread_account_id, self.account_receivable)
        self.assertEqual(wizard2.spread_journal_id.id, sales_journal)
        self.assertTrue(wizard2.spread_invoice_type_domain_ids)

    def test_03_link_invoice_line_with_spread_sheet(self):

        self.env.user.write(
            {
                "groups_id": [
                    (4, self.env.ref("analytic.group_analytic_accounting").id),
                    (4, self.env.ref("analytic.group_analytic_tags").id),
                ],
            }
        )

        Wizard = self.env["account.spread.invoice.line.link.wizard"]
        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.vendor_bill_line.id,
            default_company_id=self.env.company.id,
            allow_spread_planning=True,
        ).create({})
        self.assertEqual(wizard1.spread_action_type, "link")

        wizard1.spread_account_id = self.account_receivable
        wizard1.spread_journal_id = self.ref(
            "account_spread_cost_revenue.expenses_journal"
        )
        wizard1.spread_id = self.spread
        res_action = wizard1.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertTrue(res_action.get("res_id"))
        self.assertEqual(res_action.get("res_id"), self.spread.id)
        self.assertTrue(self.spread.invoice_line_id)
        self.assertEqual(self.spread.invoice_line_id, self.vendor_bill_line)

        self.assertFalse(any(line.move_id for line in self.spread.line_ids))

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)
            for ml in line.move_id.line_ids:
                analytic_tag = self.env.ref("analytic.tag_contract")
                self.assertEqual(ml.analytic_account_id, self.analytic_account)
                self.assertEqual(ml.analytic_tag_ids, analytic_tag)

        self.spread.invoice_id.button_cancel()

        self.assertTrue(self.spread.invoice_line_id)
        with self.assertRaises(UserError):
            self.spread.unlink()
        with self.assertRaises(UserError):
            self.spread.action_unlink_invoice_line()
        self.assertTrue(self.spread.invoice_line_id)

    def test_04_new_spread_sheet(self):

        Wizard = self.env["account.spread.invoice.line.link.wizard"]

        spread_journal_id = self.ref("account_spread_cost_revenue.expenses_journal")

        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.vendor_bill_line.id,
            default_company_id=self.env.company.id,
        ).create({"spread_action_type": "new"})
        self.assertEqual(wizard1.spread_action_type, "new")

        wizard1.write(
            {
                "spread_account_id": self.account_receivable.id,
                "spread_journal_id": spread_journal_id,
            }
        )

        res_action = wizard1.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get("res_id"))
        self.assertTrue(res_action.get("context"))
        res_context = res_action.get("context")
        self.assertTrue(res_context.get("default_name"))
        self.assertTrue(res_context.get("default_invoice_type"))
        self.assertTrue(res_context.get("default_invoice_line_id"))
        self.assertTrue(res_context.get("default_debit_account_id"))
        self.assertTrue(res_context.get("default_credit_account_id"))

        self.assertFalse(any(line.move_id for line in self.spread.line_ids))

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=self.env.company.id,
        ).create({"spread_action_type": "new"})
        self.assertEqual(wizard2.spread_action_type, "new")

        wizard2.write(
            {
                "spread_account_id": self.account_receivable.id,
                "spread_journal_id": spread_journal_id,
            }
        )

        res_action = wizard2.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get("res_id"))
        self.assertTrue(res_action.get("context"))
        res_context = res_action.get("context")
        self.assertTrue(res_context.get("default_name"))
        self.assertTrue(res_context.get("default_invoice_type"))
        self.assertTrue(res_context.get("default_invoice_line_id"))
        self.assertTrue(res_context.get("default_debit_account_id"))
        self.assertTrue(res_context.get("default_credit_account_id"))

        self.assertFalse(any(line.move_id for line in self.spread2.line_ids))

        self.spread2.compute_spread_board()
        for line in self.spread2.line_ids:
            line.create_move()
            self.assertTrue(line.move_id)

    def test_05_new_spread_sheet_from_template(self):

        Wizard = self.env["account.spread.invoice.line.link.wizard"]

        spread_account = self.account_payable
        self.assertTrue(spread_account)
        spread_journal_id = self.ref("account_spread_cost_revenue.expenses_journal")

        template = self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "purchase",
                "period_number": 5,
                "period_type": "month",
                "spread_account_id": spread_account.id,
                "spread_journal_id": spread_journal_id,
            }
        )

        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.vendor_bill_line.id,
            default_company_id=self.env.company.id,
        ).create({"spread_action_type": "template", "template_id": template.id})
        self.assertEqual(wizard1.spread_action_type, "template")

        res_action = wizard1.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertTrue(res_action.get("res_id"))

        new_spread = self.env["account.spread"].browse(res_action["res_id"])
        new_spread.compute_spread_board()

        self.assertFalse(any(line.move_id for line in new_spread.line_ids))

        for line in new_spread.line_ids:
            line.create_move()
            self.assertTrue(line.move_id)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=self.env.company.id,
        ).create({"spread_action_type": "new"})
        self.assertEqual(wizard2.spread_action_type, "new")

        wizard2.write(
            {
                "spread_account_id": spread_account.id,
                "spread_journal_id": spread_journal_id,
            }
        )

        res_action = wizard2.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get("res_id"))
        self.assertTrue(res_action.get("context"))
        res_context = res_action.get("context")
        self.assertTrue(res_context.get("default_name"))
        self.assertTrue(res_context.get("default_invoice_type"))
        self.assertTrue(res_context.get("default_invoice_line_id"))
        self.assertTrue(res_context.get("default_debit_account_id"))
        self.assertTrue(res_context.get("default_credit_account_id"))

        self.assertFalse(any(line.move_id for line in self.spread2.line_ids))

        self.spread2.compute_spread_board()
        for line in self.spread2.line_ids:
            line.create_move()
            self.assertTrue(line.move_id)

    def test_06_open_wizard(self):

        res_action = self.vendor_bill_line.spread_details()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get("res_id"))
        self.assertTrue(res_action.get("context"))

    def test_07_unlink_invoice_line_and_spread_sheet(self):

        self.assertFalse(self.spread.invoice_line_id)

        self.vendor_bill_line.spread_id = self.spread
        self.assertTrue(self.spread.invoice_line_id)
        self.spread.action_unlink_invoice_line()
        self.assertFalse(self.spread.invoice_line_id)

        self.assertFalse(self.spread2.invoice_line_id)
        self.invoice_line.spread_id = self.spread2
        self.assertTrue(self.spread2.invoice_line_id)
        self.spread2.action_unlink_invoice_line()
        self.assertFalse(self.spread2.invoice_line_id)

    def test_08_invoice_multi_line(self):
        invoice_form = Form(self.vendor_bill)
        with invoice_form.invoice_line_ids.new() as line:
            line.name = "new test line"
            line.quantity = 1.0
            line.price_unit = 1000.0
        self.invoice = invoice_form.save()
        self.assertEqual(len(self.vendor_bill.invoice_line_ids), 2)

        self.vendor_bill_line.spread_id = self.spread
        self.assertTrue(self.spread.invoice_id.invoice_line_ids[0])
        self.assertEqual(
            self.spread.invoice_id.invoice_line_ids[0], self.vendor_bill_line
        )
        self.assertTrue(self.vendor_bill_line.spread_id)
        self.assertEqual(self.vendor_bill_line.spread_check, "linked")
        self.assertFalse(self.vendor_bill.invoice_line_ids[1].spread_id)
        self.assertEqual(self.vendor_bill.invoice_line_ids[1].spread_check, "unlinked")

        self.assertFalse(any(line.move_id for line in self.spread.line_ids))

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        # Validate invoice
        self.vendor_bill.action_post()

        self.assertTrue(self.vendor_bill_line.spread_id)
        self.assertEqual(self.vendor_bill_line.spread_check, "linked")
        self.assertFalse(self.vendor_bill.invoice_line_ids[1].spread_id)
        self.assertEqual(
            self.vendor_bill.invoice_line_ids[1].spread_check, "unavailable"
        )

    def test_09_no_link_invoice(self):

        balance_sheet = self.spread.credit_account_id

        # Validate invoice
        self.vendor_bill.action_post()

        invoice_mls = self.vendor_bill.invoice_line_ids
        self.assertTrue(invoice_mls)
        for invoice_ml in invoice_mls:
            self.assertNotEqual(invoice_ml.account_id, balance_sheet)

    def test_10_link_vendor_bill_line_with_spread_sheet(self):
        invoice_form = Form(self.vendor_bill)
        with invoice_form.invoice_line_ids.new() as line:
            line.name = "new test line"
            line.quantity = 1.0
            line.price_unit = 1000.0
        self.invoice = invoice_form.save()

        self.spread.write(
            {
                "estimated_amount": 1000.0,
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 7),
                "invoice_line_id": self.vendor_bill_line.id,
                "move_line_auto_post": False,
            }
        )

        self.assertFalse(any(line.move_id for line in self.spread.line_ids))

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        expense_account = self.spread.debit_account_id
        balance_sheet = self.spread.credit_account_id
        self.assertTrue(balance_sheet.reconcile)

        spread_mls = self.spread.line_ids.mapped("move_id.line_ids")
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertEqual(spread_ml.account_id, expense_account)
            if spread_ml.credit:
                self.assertEqual(spread_ml.account_id, balance_sheet)

        # Validate invoice
        self.vendor_bill.action_post()

        count_balance_sheet = len(
            self.vendor_bill.line_ids.filtered(lambda x: x.account_id == balance_sheet)
        )
        self.assertEqual(count_balance_sheet, 1)

        self.spread.line_ids.create_and_reconcile_moves()

        spread_mls = self.spread.line_ids.mapped("move_id.line_ids")
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertFalse(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertTrue(spread_ml.full_reconcile_id)

        action_reconcile_view = self.spread2.open_reconcile_view()
        self.assertTrue(isinstance(action_reconcile_view, dict))
        self.assertFalse(action_reconcile_view.get("domain")[0][2])
        self.assertTrue(action_reconcile_view.get("context"))

    def test_11_link_vendor_bill_line_with_spread_sheet(self):
        invoice_form = Form(self.vendor_bill)
        with invoice_form.invoice_line_ids.new() as line:
            line.name = "new test line"
            line.quantity = 1.0
            line.price_unit = 1000.0
        self.invoice = invoice_form.save()
        self.spread.write(
            {
                "estimated_amount": 1000.0,
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 7),
                "invoice_line_id": self.vendor_bill_line.id,
                "move_line_auto_post": False,
            }
        )

        self.assertFalse(any(line.move_id for line in self.spread.line_ids))

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        expense_account = self.spread.debit_account_id
        balance_sheet = self.spread.credit_account_id
        self.assertTrue(balance_sheet.reconcile)

        spread_mls = self.spread.line_ids.mapped("move_id.line_ids")
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertEqual(spread_ml.account_id, expense_account)
            if spread_ml.credit:
                self.assertEqual(spread_ml.account_id, balance_sheet)

        # Validate invoice
        self.vendor_bill.action_post()

        invoice_mls = self.vendor_bill.line_ids
        self.assertTrue(invoice_mls)

        count_balance_sheet = len(
            invoice_mls.filtered(lambda x: x.account_id == balance_sheet)
        )
        self.assertEqual(count_balance_sheet, 1)

        self.spread.company_id.force_move_auto_post = True
        self.spread.line_ids.create_and_reconcile_moves()

        spread_mls = self.spread.line_ids.mapped("move_id.line_ids")
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.credit:
                self.assertEqual(spread_ml.account_id, balance_sheet)
                self.assertTrue(spread_ml.full_reconcile_id)
            if spread_ml.debit:
                self.assertEqual(spread_ml.account_id, expense_account)
                self.assertFalse(spread_ml.full_reconcile_id)

        action_reconcile_view = self.spread.open_reconcile_view()
        self.assertTrue(isinstance(action_reconcile_view, dict))
        self.assertTrue(action_reconcile_view.get("domain")[0][2])
        self.assertTrue(action_reconcile_view.get("context"))

        action_spread_details = self.vendor_bill_line.spread_details()
        self.assertTrue(isinstance(action_spread_details, dict))
        self.assertTrue(action_spread_details.get("res_id"))

    def test_12_link_invoice_line_with_spread_sheet_full_reconcile(self):

        # Validate invoice
        self.sale_invoice.action_post()

        self.spread2.write(
            {
                "estimated_amount": 1000.0,
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 7),
                "invoice_line_id": self.invoice_line.id,
                "move_line_auto_post": False,
            }
        )

        self.assertFalse(any(line.move_id for line in self.spread2.line_ids))

        self.spread2.compute_spread_board()
        spread_lines = self.spread2.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        payable_account = self.spread2.credit_account_id
        balance_sheet = self.spread2.debit_account_id
        self.assertTrue(balance_sheet.reconcile)

        spread_mls = self.spread2.line_ids.mapped("move_id.line_ids")
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertEqual(spread_ml.account_id, balance_sheet)
                self.assertTrue(spread_ml.reconciled)
                self.assertTrue(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertEqual(spread_ml.account_id, payable_account)
                self.assertFalse(spread_ml.reconciled)
                self.assertFalse(spread_ml.full_reconcile_id)

        invoice_mls = self.sale_invoice.invoice_line_ids
        self.assertTrue(invoice_mls)
        for invoice_ml in invoice_mls:
            self.assertEqual(invoice_ml.account_id, balance_sheet)

        action_reconcile_view = self.spread2.open_reconcile_view()
        self.assertTrue(isinstance(action_reconcile_view, dict))
        self.assertTrue(action_reconcile_view.get("domain")[0][2])
        self.assertFalse(action_reconcile_view.get("res_id"))
        self.assertTrue(action_reconcile_view.get("context"))

        action_spread_details = self.invoice_line.spread_details()
        self.assertTrue(isinstance(action_spread_details, dict))
        self.assertTrue(action_spread_details.get("res_id"))

    def test_13_link_invoice_line_with_spread_sheet_partial_reconcile(self):

        self.spread2.write(
            {
                "estimated_amount": 1000.0,
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 7),
            }
        )

        self.spread2.compute_spread_board()
        spread_lines = self.spread2.line_ids
        self.assertEqual(len(spread_lines), 13)
        self.assertFalse(any(line.move_id for line in spread_lines))

        spread_lines[0].create_and_reconcile_moves()
        spread_lines[1].create_and_reconcile_moves()
        spread_lines[2].create_and_reconcile_moves()
        spread_lines[3].create_and_reconcile_moves()

        self.assertEqual(spread_lines[0].move_id.state, "posted")
        self.assertEqual(spread_lines[1].move_id.state, "posted")
        self.assertEqual(spread_lines[2].move_id.state, "posted")
        self.assertEqual(spread_lines[3].move_id.state, "posted")
        self.assertNotEqual(spread_lines[4].move_id.state, "posted")

        spread_mls = spread_lines[0].move_id.line_ids
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertFalse(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertFalse(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)

        balance_sheet = self.spread2.debit_account_id
        self.assertTrue(balance_sheet.reconcile)

        # Assing invoice line to spread
        self.spread2.invoice_line_id = self.invoice_line
        self.assertEqual(self.invoice_line.spread_id, self.spread2)

        # Validate invoice
        self.sale_invoice.action_post()
        invoice_mls = self.sale_invoice.invoice_line_ids
        self.assertTrue(invoice_mls)
        for invoice_ml in invoice_mls:
            self.assertEqual(invoice_ml.account_id, balance_sheet)

        spread_lines = self.spread2.line_ids
        spread_lines[4].create_and_reconcile_moves()

        self.assertEqual(spread_lines[4].move_id.state, "posted")

        spread_mls = spread_lines[4].move_id.line_ids
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertTrue(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertFalse(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)

        other_journal = self.env["account.journal"].create(
            {"name": "Other Journal", "type": "general", "code": "test2"}
        )
        with self.assertRaises(ValidationError):
            self.spread2.journal_id = other_journal

        with self.assertRaises(UserError):
            self.spread2.unlink()

    def test_14_create_all_moves(self):
        self.spread.compute_spread_board()

        self.assertEqual(len(self.spread.line_ids), 12)
        self.assertFalse(any(line.move_id for line in self.spread.line_ids))

        # create moves for all the spread lines
        self.spread.create_all_moves()
        self.assertTrue(all(line.move_id for line in self.spread.line_ids))

        with self.assertRaises(ValidationError):
            self.spread.unlink()

    def test_15_invoice_refund(self):

        self.vendor_bill_line.spread_id = self.spread

        # Validate invoice
        self.vendor_bill.action_post()
        self.assertTrue(self.vendor_bill.invoice_line_ids.mapped("spread_id"))

        # Create a refund for invoice.
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=self.vendor_bill.ids)
            .create(
                {
                    "date": fields.Date.today(),
                    "reason": "no reason",
                    "refund_method": "refund",
                }
            )
        )
        reversal = move_reversal.reverse_moves()
        refund = self.env["account.move"].browse(reversal["res_id"])
        self.assertFalse(refund.invoice_line_ids.mapped("spread_id"))
