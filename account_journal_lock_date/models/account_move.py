# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscal_lock_dates(self):
        res = super()._check_fiscal_lock_dates()
        if self.env.context.get("bypass_journal_lock_date"):
            return res

        is_manager = self.env.user.has_group("account.group_account_manager")
        for move in self:
            if move.date <= move.journal_id.user_journal_lock_date:
                formatted_lock_date = format_date(
                    self.env, move.journal_id.user_journal_lock_date
                )
                if is_manager:
                    message = self.env._(
                        "You cannot add/modify entries for the journal '%(journal)s' "
                        "prior to and inclusive of the lock date %(journal_date)s",
                        journal=move.journal_id.display_name,
                        journal_date=formatted_lock_date,
                    )
                else:
                    message = self.env._(
                        "You cannot add/modify entries for the journal '%(journal)s' "
                        "prior to and inclusive of the lock date %(journal_date)s. "
                        "Check the Journal settings or ask someone "
                        "with the 'Adviser' role",
                        journal=move.journal_id.display_name,
                        journal_date=formatted_lock_date,
                    )
                raise UserError(message)
        return res
