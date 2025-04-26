# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from datetime import date

from odoo import api, fields, models


class AccountInvoiceSpreadLine(models.Model):
    _inherit = "account.spread.line"

    @api.model
    def _create_entries(self):
        """
        OVERRIDE for search line excluding date before locked date
        Find spread line entries where date is in the past and
        create moves for them. Method also called by the cron job.
        """
        lock_date = max(
            self.env.company.period_lock_date or date.min,
            self.env.company.fiscalyear_lock_date or date.min,
        )
        domain = self._get_spread_line_domain(lock_date)
        lines = self.search(domain)
        lines.create_and_reconcile_moves()

        unposted_moves = (
            self.search([("move_id", "!=", False)])
            .mapped("move_id")
            .filtered(lambda m: m.state != "posted")
        )
        unposted_moves.filtered(
            lambda m: m.company_id.force_move_auto_post
        ).action_post()

        spreads_to_archive = (
            self.env["account.spread"]
            .search([("all_posted", "=", True)])
            .filtered(lambda s: s.company_id.auto_archive_spread)
        )
        spreads_to_archive.write({"active": False})

    @api.model
    def _get_spread_line_domain(self, lock_date):
        """
        Hook method to define the domain for searching spread lines.
        """
        return [
            ("date", ">", lock_date),
            ("date", "<=", fields.Date.today()),
            ("move_id", "=", False),
        ]
