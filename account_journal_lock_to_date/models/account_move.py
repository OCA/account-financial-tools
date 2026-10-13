# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

from odoo.addons.account.models.account_move import BYPASS_LOCK_CHECK


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_journal_lock_to_date(self):
        """Return the lock to date of the journal applicable to the current user"""
        self.ensure_one()
        journal = self.journal_id
        if self.env.user.has_group("account.group_account_manager"):
            return journal.fiscalyear_lock_to_date
        lock_to_dates = [
            lock_to_date
            for lock_to_date in (
                journal.fiscalyear_lock_to_date,
                journal.period_lock_to_date,
            )
            if lock_to_date
        ]
        return min(lock_to_dates) if lock_to_dates else False

    def _check_fiscal_lock_dates(self):
        res = super()._check_fiscal_lock_dates()
        if (
            self.env.context.get("bypass_journal_lock_to_date")
            or self.env.context.get("bypass_lock_check") is BYPASS_LOCK_CHECK
        ):
            return res
        is_adviser = self.env.user.has_group("account.group_account_manager")
        for move in self:
            lock_to_date = move._get_journal_lock_to_date()
            if not lock_to_date or not move.date or move.date < lock_to_date:
                continue
            if is_adviser:
                message = self.env._(
                    "You cannot add/modify entries for the journal '%(journal)s' "
                    "posterior to and inclusive of the lock to date "
                    "%(journal_date)s",
                    journal=move.journal_id.display_name,
                    journal_date=format_date(self.env, lock_to_date),
                )
            else:
                message = self.env._(
                    "You cannot add/modify entries for the journal '%(journal)s' "
                    "posterior to and inclusive of the lock to date "
                    "%(journal_date)s. Check the Journal settings or ask "
                    "someone with the 'Adviser' role",
                    journal=move.journal_id.display_name,
                    journal_date=format_date(self.env, lock_to_date),
                )
            raise UserError(message)
        return res
