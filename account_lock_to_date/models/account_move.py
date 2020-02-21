# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def _check_lock_date(self):
        res = super()._check_lock_date()
        for move in self:
            lock_to_date = min(
                move.company_id.period_lock_to_date,
                move.company_id.fiscalyear_lock_to_date) or False
            if self.user_has_groups('account.group_account_manager'):
                lock_to_date = move.company_id.fiscalyear_lock_to_date or False
            if lock_to_date and move.date >= lock_to_date:
                if self.user_has_groups('account.group_account_manager'):
                    message = _("You cannot add/modify entries after and "
                                "inclusive of the lock to date %s") % (
                        lock_to_date)
                else:
                    message = _("You cannot add/modify entries after and "
                                "inclusive of the lock to date %s. "
                                "Check the company settings or ask someone "
                                "with the 'Adviser' role") % (
                        lock_to_date)
                raise UserError(message)
        return res
