# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class AccountMove(models.Model):

    _inherit = "account.move"

    def write(self, values):
        res = super().write(values)
        self._check_fiscalyear_lock_date()
        return res

    def _check_fiscalyear_lock_date(self):
        res = super()._check_fiscalyear_lock_date()
        if self.env.context.get("bypass_journal_lock_date"):
            return res
        for move in self:
            if self.user_has_groups("account.group_account_manager"):
                lock_date = move.journal_id.fiscalyear_lock_date or date.min
            else:
                lock_date = max(
                    move.journal_id.period_lock_date or date.min,
                    move.journal_id.fiscalyear_lock_date or date.min,
                )
            if move.date <= lock_date:
                lock_date = format_date(self.env, lock_date)
                if self.user_has_groups("account.group_account_manager"):
                    message = _(
                        "You cannot add/modify entries for the journal '%(journal)s' "
                        "prior to and inclusive of the lock date %(journal_date)s"
                    ) % {
                        "journal": move.journal_id.display_name,
                        "journal_date": lock_date,
                    }
                else:
                    message = _(
                        "You cannot add/modify entries for the journal '%(journal)s' "
                        "prior to and inclusive of the lock date %(journal_date)s. "
                        "Check the Journal settings or ask someone "
                        "with the 'Adviser' role"
                    ) % {
                        "journal": move.journal_id.display_name,
                        "journal_date": lock_date,
                    }
                raise UserError(message)
        return res
