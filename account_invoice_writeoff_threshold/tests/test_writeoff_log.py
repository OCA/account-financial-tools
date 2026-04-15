from .common import TestWriteoffCommon


class TestWriteoffLog(TestWriteoffCommon):
    def test_log_state_is_done_after_sync_execution(self):
        """Synchronous execution must set log state to 'done'."""
        log = self.env["account.writeoff.log"].run_writeoff()
        self.assertEqual(log.state, "done")

    def test_log_totals_are_consistent_with_lines(self):
        """total_lines and total_amount must match line records."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 97.5)

        log = self.env["account.writeoff.log"].run_writeoff()

        self.assertEqual(log.total_lines, len(log.line_ids))
        self.assertAlmostEqual(log.total_amount, sum(log.line_ids.mapped("amount")))

    def test_log_company_is_current_company(self):
        log = self.env["account.writeoff.log"].run_writeoff()
        self.assertEqual(log.company_id, self.company)

    def test_log_writeoff_date_defaults_to_today(self):
        """When no writeoff_date is passed, log records today's date."""
        from odoo import fields

        log = self.env["account.writeoff.log"].run_writeoff()
        self.assertEqual(log.writeoff_date, fields.Date.today())

    def test_log_writeoff_date_is_stored(self):
        """A custom writeoff_date must be stored on the log."""
        from odoo import fields

        custom_date = fields.Date.from_string("2026-01-15")
        log = self.env["account.writeoff.log"].run_writeoff(writeoff_date=custom_date)
        self.assertEqual(log.writeoff_date, custom_date)

    def test_log_date_filters_are_stored(self):
        """date_from and date_to must be stored on the log."""
        from odoo import fields

        date_from = fields.Date.from_string("2026-01-01")
        date_to = fields.Date.from_string("2026-03-31")
        log = self.env["account.writeoff.log"].run_writeoff(
            date_from=date_from, date_to=date_to
        )
        self.assertEqual(log.date_from, date_from)
        self.assertEqual(log.date_to, date_to)

    def test_dispatch_writeoff_calls_process_batch(self):
        """_dispatch_writeoff in base module calls _process_batch synchronously."""
        invoice = self._create_posted_invoice("out_invoice", amount=100.0)
        self._partial_pay(invoice, 98.0)
        candidates = self.env["account.writeoff.log"]._get_candidate_lines(self.company)
        log = self.env["account.writeoff.log"].create(
            {
                "threshold_amount": 10.0,
                "company_id": self.company.id,
            }
        )
        self.env["account.writeoff.log"]._dispatch_writeoff(log, candidates)
        self.assertEqual(log.state, "done")
        self.assertEqual(log.total_lines, 1)
