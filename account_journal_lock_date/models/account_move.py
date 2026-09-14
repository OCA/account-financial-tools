# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscal_lock_dates(self):
        res = super()._check_fiscal_lock_dates()
        if self.env.context.get("bypass_journal_lock_date"):
            return res

        date_min = fields.date.min
        for move in self:
            if self.env.user.has_group("account.group_account_manager"):
                lock_date = move.journal_id.fiscalyear_lock_date or date_min
            else:
                lock_date = max(
                    move.journal_id.period_lock_date or date_min,
                    move.journal_id.fiscalyear_lock_date or date_min,
                )
            if move.date <= lock_date:
                lock_date = format_date(self.env, lock_date)
                if self.env.user.has_group("account.group_account_manager"):
                    message = self.env._(
                        "You cannot add/modify entries for the journal '%(journal)s' "
                        "prior to and inclusive of the lock date %(journal_date)s",
                        journal=move.journal_id.display_name,
                        journal_date=lock_date,
                    )
                else:
                    message = self.env._(
                        "You cannot add/modify entries for the journal '%(journal)s' "
                        "prior to and inclusive of the lock date %(journal_date)s. "
                        "Check the Journal settings or ask someone "
                        "with the 'Adviser' role",
                        journal=move.journal_id.display_name,
                        journal_date=lock_date,
                    )
                raise UserError(message)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.filtered(
            lambda x: x.journal_id.lock_date_restrict_creation
        )._check_fiscal_lock_dates()
        return res
