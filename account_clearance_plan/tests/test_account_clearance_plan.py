# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountClearancePlan(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.general_journal = cls.company_data["default_journal_misc"]
        cls.cash_journal = cls.company_data["default_journal_cash"]
        cls.company_data["company"].clearance_plan_journal_id = cls.general_journal
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "journal_id": cls.company_data["default_journal_sale"].id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Line",
                            "price_unit": 1000.0,
                            "quantity": 1,
                            "tax_ids": False,
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()
        cls.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=[cls.invoice.id],
        ).create(
            {
                "amount": 200.0,
                "journal_id": cls.cash_journal.id,
            }
        ).action_create_payments()
        cls.invoice_ctx = {
            "active_model": "account.move",
            "active_ids": [cls.invoice.id],
        }

    def create_and_fill_wizard(self):
        clearance_plan_wizard = Form(
            self.env["account.clearance.plan"].with_context(**self.invoice_ctx)
        )
        i = 1
        while i <= 4:
            with clearance_plan_wizard.clearance_plan_line_ids.new() as line:
                line.amount = 200.0
                line.date_maturity = fields.Date.today() + timedelta(days=30 * i)
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
            line.date_maturity = fields.Date.today()
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
                    lambda move_line, clearance_line=line: move_line.debit
                    == clearance_line.amount
                    and move_line.date_maturity == clearance_line.date_maturity
                )
            )
        for line in self.invoice.line_ids.filtered(
            lambda move_line: move_line.account_id.account_type
            in ("asset_receivable", "liability_payable")
        ):
            self.assertTrue(line.reconciled)
            for reconciled_line in line.full_reconcile_id.reconciled_line_ids.filtered(
                lambda reconciled_line, move_line=line: reconciled_line.credit
                == move_line.debit
            ):
                self.assertEqual(reconciled_line.move_id.id, move.id)
