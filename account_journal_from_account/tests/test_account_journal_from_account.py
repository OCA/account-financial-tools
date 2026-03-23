# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountJournalFromAccount(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.bank_account = cls.env["account.account"].create(
            {
                "name": "Test Bank Account",
                "code": "TESTBANK999",
                "account_type": "asset_cash",
                "company_ids": [Command.set([cls.company.id])],
            }
        )
        cls.inbound_payment_method = cls.env.ref(
            "account.account_payment_method_manual_in"
        )
        cls.outbound_payment_method = cls.env.ref(
            "account.account_payment_method_manual_out"
        )

    def test_01_create_journal_from_account(self):
        """Test creating a journal directly from a bank account."""
        action = self.bank_account.action_create_journal()
        self.assertTrue(action)
        self.assertEqual(action.get("res_model"), "account.journal")
        journal = self.env["account.journal"].search(
            [("default_account_id", "=", self.bank_account.id)]
        )
        self.assertTrue(journal)
        self.assertEqual(journal.type, "bank")

    def test_02_duplicate_journal_warning(self):
        """Test the duplicate journal warning wizard."""
        self.bank_account.action_create_journal()
        action = self.bank_account.action_create_journal()
        self.assertTrue(action)
        self.assertEqual(action.get("res_model"), "user.confirmation.wizard")
        wizard = (
            self.env["user.confirmation.wizard"]
            .with_context(**action.get("context"))
            .create({})
        )
        wizard.action_confirm()
        journals = self.env["account.journal"].search(
            [("default_account_id", "=", self.bank_account.id)]
        )
        self.assertEqual(len(journals), 2)

    def test_03_create_journal_invalid_account_type(self):
        """Test creating a journal from an invalid account type (e.g., income)."""
        income_account = self.env["account.account"].create(
            {
                "name": "Test Income Account",
                "code": "TESTINC999",
                "account_type": "income",
                "company_ids": [Command.set([self.company.id])],
            }
        )
        with self.assertRaises(ValidationError):
            income_account.action_create_journal()

    def test_04_payment_account_configuration(self):
        """Test whether inbound/outbound payment accounts are automatically set."""
        inbound_account = self.env["account.account"].create(
            {
                "name": "Outstanding Receipts",
                "code": "OUTREC999",
                "account_type": "asset_current",
                "company_ids": [Command.set([self.company.id])],
            }
        )
        outbound_account = self.env["account.account"].create(
            {
                "name": "Outstanding Payments",
                "code": "OUTPAY999",
                "account_type": "liability_current",
                "company_ids": [Command.set([self.company.id])],
            }
        )
        self.env["res.config.settings"].create(
            {
                "inbound_payment_account_id": inbound_account.id,
                "outbound_payment_account_id": outbound_account.id,
            }
        ).execute()
        action = self.bank_account.action_create_journal()
        journal_id = action.get("res_id")
        journal = self.env["account.journal"].browse(journal_id)
        inbound_line = journal.inbound_payment_method_line_ids.filtered(
            lambda line: line.payment_method_id == self.inbound_payment_method
        )
        outbound_line = journal.outbound_payment_method_line_ids.filtered(
            lambda line: line.payment_method_id == self.outbound_payment_method
        )

        if inbound_line:
            self.assertEqual(inbound_line.payment_account_id, inbound_account)
        if outbound_line:
            self.assertEqual(outbound_line.payment_account_id, outbound_account)
