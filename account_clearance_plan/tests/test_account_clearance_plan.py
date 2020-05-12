# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, Form
from odoo.exceptions import ValidationError

from datetime import datetime, timedelta


class TestAccountClearancePlan(TransactionCase):
    def setUp(self):
        super(TestAccountClearancePlan, self).setUp()
        self.company = self.env.ref("base.main_company")
        self.partner = self.env["res.partner"].create({"name": "Test"})
        self.account_type_receivable = self.env["account.account.type"].create(
            {"name": "Test Receivable", "type": "receivable"}
        )
        self.account_type_regular = self.env["account.account.type"].create(
            {"name": "Test Regular", "type": "other"}
        )
        self.account_receivable = self.env["account.account"].create(
            {
                "name": "Test Receivable",
                "code": "TEST_AR",
                "user_type_id": self.account_type_receivable.id,
                "reconcile": True,
            }
        )
        self.account_income = self.env["account.account"].create(
            {
                "name": "Test Income",
                "code": "TEST_IN",
                "user_type_id": self.account_type_regular.id,
                "reconcile": False,
            }
        )
        self.sale_journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", self.company.id)]
        )[0]
        self.cash_journal = self.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", self.company.id)]
        )[0]
        self.general_journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company.id)]
        )[0]
        self.company.clearance_plan_journal_id = self.general_journal
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        self.invoice_line = self.env["account.invoice.line"].create(
            {
                "name": "Line",
                "price_unit": 1000.0,
                "account_id": self.account_income.id,
                "quantity": 1,
            }
        )
        self.invoice = self.env["account.invoice"].create(
            {
                "name": "Test Customer Invoice",
                "journal_id": self.sale_journal.id,
                "partner_id": self.partner.id,
                "account_id": self.account_receivable.id,
                "invoice_line_ids": [(4, self.invoice_line.id)],
            }
        )
        self.invoice.action_invoice_open()
        self.invoice_ctx = {
            "active_model": "account.invoice",
            "active_ids": [self.invoice.id],
        }
        self.register_payments = (
            self.env["account.register.payments"]
            .with_context(self.invoice_ctx)
            .create(
                {
                    "payment_date": datetime.now().strftime("%Y-%m-%d"),
                    "payment_method_id": self.payment_method_manual_in.id,
                    "journal_id": self.cash_journal.id,
                    "amount": 200.0,
                }
            )
        )
        self.register_payments.create_payments()

    def create_and_fill_wizard(self):
        clearance_plan_wizard = Form(
            self.env["account.clearance.plan"].with_context(self.invoice_ctx)
        )
        i = 1
        while i <= 4:
            with clearance_plan_wizard.clearance_plan_line_ids.new() as line:
                line.amount = 200.0
                line.date_maturity = (datetime.now() + timedelta(days=30 * i)).strftime(
                    "%Y-%m-%d"
                )
            i += 1
        return clearance_plan_wizard

    def test_wizard_values(self):
        clearance_plan = self.create_and_fill_wizard().save()
        self.assertEqual(clearance_plan.journal_id.id, self.general_journal.id)
        self.assertEqual(clearance_plan.amount_to_allocate, 800.0)
        self.assertEqual(clearance_plan.amount_unallocated, 0.0)

    def test_wizard_negative_amount(self):
        clearance_plan_wizard = self.create_and_fill_wizard()
        with clearance_plan_wizard.clearance_plan_line_ids.new() as line:
            line.amount = -200.0
            line.date_maturity = datetime.now().strftime("%Y-%m-%d")
        with self.assertRaises(ValidationError):
            clearance_plan_wizard.save()

    def test_confirm_clearance_plan(self):
        clearance_plan = self.create_and_fill_wizard().save()
        res = clearance_plan.confirm_plan()
        move = self.env["account.move"].browse(res["res_id"])
        self.assertEqual(move.journal_id, clearance_plan.journal_id)
        for line in clearance_plan.clearance_plan_line_ids:
            self.assertTrue(
                move.line_ids.filtered(
                    lambda l: l.debit == line.amount
                    and l.date_maturity == line.date_maturity
                )
            )
        for line in self.invoice.move_id.line_ids.filtered(
            lambda l: l.account_id == self.invoice.account_id
        ):
            self.assertTrue(line.reconciled)
            for reconciled_line in line.full_reconcile_id.reconciled_line_ids.filtered(
                lambda l: l.credit == line.debit
            ):
                self.assertEqual(reconciled_line.move_id.id, move.id)
