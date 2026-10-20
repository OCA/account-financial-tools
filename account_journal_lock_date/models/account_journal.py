# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    fiscalyear_lock_date = fields.Date(
        string="Lock Date",
        help="No users, including Advisers, can edit accounts prior "
        "to and inclusive of this date for this journal. Use it "
        "for fiscal year locking for this journal, for example.",
    )
    period_lock_date = fields.Date(
        string="Lock Date for Non-Advisers",
        help="Only users with the 'Adviser' role can edit accounts "
        "prior to and inclusive of this date for this journal. "
        "Use it for period locking inside an open fiscal year "
        "for this journal, for example.",
    )

    user_journal_lock_date = fields.Date(compute="_compute_user_journal_lock_date")

    @api.depends("fiscalyear_lock_date", "period_lock_date")
    @api.depends_context("uid")
    def _compute_user_journal_lock_date(self):
        date_min = date.min
        is_manager = self.env.user.has_group("account.group_account_manager")
        for journal in self:
            if is_manager:
                lock_date = journal.fiscalyear_lock_date or date_min
            else:
                lock_date = max(
                    journal.period_lock_date or date_min,
                    journal.fiscalyear_lock_date or date_min,
                )
            journal.user_journal_lock_date = lock_date
