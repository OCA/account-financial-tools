# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestMoveReverseReconcile(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.invoice = cls._create_invoice(move_type="out_invoice", post=True)
        cls.credit_note = cls.invoice._reverse_moves()

    def test_posting_reversal_reconciles_invoice(self):
        self.assertEqual(
            self.credit_note.reversal_post_automatic_reconcile, "reconcile"
        )
        self.credit_note.action_post()

        invoice_receivable = self.invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        credit_note_receivable = self.credit_note.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )

        self.assertTrue(invoice_receivable.reconciled)
        self.assertTrue(credit_note_receivable.reconciled)
        self.assertEqual(
            invoice_receivable.matched_credit_ids.credit_move_id, credit_note_receivable
        )
        self.assertEqual(
            credit_note_receivable.matched_debit_ids.debit_move_id, invoice_receivable
        )

    def test_posting_partial_reversal_reconciles_invoice(self):
        self.assertEqual(
            self.credit_note.reversal_post_automatic_reconcile, "reconcile"
        )
        self.credit_note.invoice_line_ids[:1].unlink()
        self.credit_note.action_post()

        invoice_receivable = self.invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        credit_note_receivable = self.credit_note.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )

        self.assertEqual(
            invoice_receivable.matched_credit_ids.credit_move_id, credit_note_receivable
        )
        self.assertEqual(
            credit_note_receivable.matched_debit_ids.debit_move_id, invoice_receivable
        )

    def test_posting_reversal_fully_reconciles_invoice(self):
        self.credit_note.reversal_post_automatic_reconcile = "full_amount_reconcile"
        self.credit_note.action_post()

        invoice_receivable = self.invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        credit_note_receivable = self.credit_note.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )

        self.assertTrue(invoice_receivable.reconciled)
        self.assertTrue(credit_note_receivable.reconciled)
        self.assertEqual(
            invoice_receivable.matched_credit_ids.credit_move_id, credit_note_receivable
        )
        self.assertEqual(
            credit_note_receivable.matched_debit_ids.debit_move_id, invoice_receivable
        )

    def test_posting_partial_reversal_not_reconciles_invoice(self):
        self.credit_note.reversal_post_automatic_reconcile = "full_amount_reconcile"
        self.credit_note.invoice_line_ids[:1].unlink()
        self.credit_note.action_post()

        invoice_receivable = self.invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        credit_note_receivable = self.credit_note.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        self.assertFalse(invoice_receivable.reconciled)
        self.assertFalse(credit_note_receivable.reconciled)
        self.assertFalse(invoice_receivable.matched_credit_ids.credit_move_id)
        self.assertFalse(credit_note_receivable.matched_debit_ids.debit_move_id)

    def test_posting_reversal_not_reconciles_invoice(self):
        """Posting a reversal should reconcile its receivable line with the invoice."""
        self.credit_note.reversal_post_automatic_reconcile = "no_reconcile"
        self.credit_note.action_post()
        self.assertEqual(self.credit_note.state, "posted")

        invoice_receivable = self.invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        credit_note_receivable = self.credit_note.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )

        self.assertFalse(invoice_receivable.reconciled)
        self.assertFalse(credit_note_receivable.reconciled)
        self.assertFalse(invoice_receivable.matched_credit_ids.credit_move_id)
        self.assertFalse(credit_note_receivable.matched_debit_ids.debit_move_id)

    def test_journal_settings_apply(self):
        self.credit_note.button_cancel()
        journal = self.invoice.journal_id
        self.assertEqual(journal.reversal_post_automatic_reconcile_default, "reconcile")
        journal.reversal_post_automatic_reconcile_default = "full_amount_reconcile"
        credit_note = self.invoice._reverse_moves()
        self.assertEqual(credit_note.reversal_post_automatic_reconcile, "full_amount_reconcile")
