# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def _check_lock_date(self):
        for move in self:
            if move.company_id.permanent_lock_date \
                    and move.date <= move.company_id.permanent_lock_date:
                raise UserError(_(
                    "You cannot add/modify entries prior to and inclusive "
                    "of the permanent lock date."))
        return super(AccountMove, self)._check_lock_date()

    @api.multi
    def button_cancel(self):
        # Add check for button_cancel, as it does not use ORM
        self._check_lock_date()
        return super(AccountMove, self).button_cancel()

    @api.model
    def create(self, vals):
        # Add _check_lock_date for create of account.move,
        # as it is not done by default
        result = super(AccountMove, self).create(vals)
        result._check_lock_date()
        return result

    @api.multi
    def write(self, vals):
        # Add _check_lock_date for write of account.move,
        # as it is not done by default
        self._check_lock_date()
        result = super(AccountMove, self).write(vals)
        return result
