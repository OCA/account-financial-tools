# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import _, api, models
from openerp.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def _check_lock_date(self):
        for move in self:
            if move.date <= move.company_id.permanent_lock_date:
                raise UserError(_(
                    "You cannot add/modify entries prior to and inclusive "
                    "of the permanent lock date."))
        return super(AccountMove, self)._check_lock_date()

    @api.multi
    def button_cancel(self):
        # Add check for button_cancel, as it does not use ORM
        self._check_lock_date()
        return super(AccountMove, self).button_cancel()
