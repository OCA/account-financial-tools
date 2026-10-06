from odoo import fields
from odoo.exceptions import UserError

from .common import TestWriteoffCommon


class TestWriteoffThreshold(TestWriteoffCommon):
    def test_customer_invoice_below_threshold_becomes_paid(self):
        """Customer invoice with residual < threshold is fully reconciled."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 95.0)
        self.assertAlmostEqual(invoice.amount_residual, 5.0)

        self.env["account.writeoff.log"].run_writeoff()

        self.assertEqual(invoice.payment_state, "paid")
        self.assertAlmostEqual(invoice.amount_residual, 0.0)

    def test_vendor_bill_below_threshold_becomes_paid(self):
        """Vendor bill with residual < threshold is fully reconciled."""
        bill = self._create_posted_invoice("in_invoice", amount=200.0)
        self._partial_pay(bill, 196.0)
        self.assertAlmostEqual(bill.amount_residual, 4.0)

        self.env["account.writeoff.log"].run_writeoff()

        self.assertEqual(bill.payment_state, "paid")
        self.assertAlmostEqual(bill.amount_residual, 0.0)

    def test_residual_at_or_above_threshold_is_not_touched(self):
        """Residual >= threshold must not be written off."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 90.0)  # leaves 10.0 == threshold
        residual_before = invoice.amount_residual

        self.env["account.writeoff.log"].run_writeoff()

        self.assertAlmostEqual(invoice.amount_residual, residual_before)

    def test_fully_paid_invoice_is_never_a_candidate(self):
        """Fully paid invoices must not appear in candidates."""
        invoice = self._create_posted_invoice("out_invoice", amount=50.0)
        self._partial_pay(invoice, 50.0)
        self.assertEqual(invoice.payment_state, "paid")

        self.env["account.writeoff.log"].run_writeoff()

        self.assertEqual(invoice.payment_state, "paid")

    def test_customer_writeoff_uses_income_account(self):
        """Write-off entry for a customer invoice targets the income account."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 97.0)

        log = self.env["account.writeoff.log"].run_writeoff()

        accounts = log.line_ids[0].writeoff_move_id.line_ids.mapped("account_id")
        self.assertIn(self.income_account, accounts)

    def test_vendor_writeoff_uses_expense_account(self):
        """Write-off entry for a vendor bill targets the expense account."""
        bill = self._create_posted_invoice("in_invoice", amount=100.0)
        self._partial_pay(bill, 93.0)

        log = self.env["account.writeoff.log"].run_writeoff()

        accounts = log.line_ids[0].writeoff_move_id.line_ids.mapped("account_id")
        self.assertIn(self.expense_account, accounts)

    def test_incomplete_config_raises_user_error(self):
        """Missing income account must raise UserError."""
        self.company.writeoff_income_account_id = False

        with self.assertRaises(UserError):
            self.env["account.writeoff.log"].run_writeoff()

    def test_no_candidates_creates_empty_log(self):
        """With no qualifying moves, a log is still created with zero lines."""
        log = self.env["account.writeoff.log"].run_writeoff()
        self.assertEqual(log.total_lines, 0)
        self.assertAlmostEqual(log.total_amount, 0.0)

    def test_process_batch_is_idempotent_on_empty_list(self):
        """_process_batch with empty list must not raise."""
        log = self.env["account.writeoff.log"].create(
            {
                "threshold_amount": 10.0,
                "company_id": self.company.id,
            }
        )
        self.env["account.writeoff.log"]._process_batch(log.id, [])
        self.assertEqual(log.total_lines, 0)

    def test_date_filter_excludes_moves_outside_range(self):
        """Moves outside date_from/date_to must not be written off."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 95.0)

        future_date = fields.Date.from_string("2099-01-01")
        log = self.env["account.writeoff.log"].run_writeoff(
            date_from=future_date, date_to=future_date
        )

        self.assertEqual(log.total_lines, 0)
        self.assertAlmostEqual(invoice.amount_residual, 5.0)

    def test_writeoff_date_is_used_on_journal_entry(self):
        """The writeoff_date must be set on the write-off journal entry."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 97.0)
        entry_date = fields.Date.from_string("2026-01-15")

        log = self.env["account.writeoff.log"].run_writeoff(writeoff_date=entry_date)

        self.assertEqual(log.line_ids[0].writeoff_move_id.date, entry_date)

    def test_wizard_skip_excludes_line_from_writeoff(self):
        """A line marked skip=True must not be processed by action_confirm."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 97.0)

        wizard = self.env["account.writeoff.threshold.wizard"].create(
            {"company_id": self.company.id}
        )
        wizard.action_preview()
        wizard.preview_line_ids.write({"skip": True})
        log = self.env["account.writeoff.log"].create(
            {
                "threshold_amount": self.company.writeoff_threshold_amount,
                "company_id": self.company.id,
                "state": "draft",
                "writeoff_date": fields.Date.today(),
            }
        )
        candidates = self.env["account.move.line"].browse(
            wizard.preview_line_ids.filtered(lambda line: not line.skip)
            .mapped("move_line_id")
            .ids
        )
        self.env["account.writeoff.log"]._dispatch_writeoff(log, candidates)
        self.assertEqual(log.total_lines, 0)
        self.assertNotEqual(invoice.payment_state, "paid")
