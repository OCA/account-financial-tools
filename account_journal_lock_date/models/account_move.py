# Copyright 2017 ACSONE SA/NV
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

from ..exceptions import JournalLockDateError


class AccountMove(models.Model):
    _inherit = 'account.move'

    can_be_locked = fields.Boolean(
        'Can be locked', compute="_compute_can_be_locked", store=True)
    locked = fields.Boolean('Locked', readonly=True)

    @api.multi
    @api.depends('company_id', 'journal_id', 'date', 'locked')
    def _compute_can_be_locked(self):
        for move in self:
            if move.locked:
                move.can_be_locked = False
            else:
                fy_lock_date = move.company_id.fiscalyear_lock_date
                journal_lock_date = move.journal_id.lock_date
                lock_date = max(fy_lock_date or '0000-00-00',
                                journal_lock_date or '0000-00-00')
                move.can_be_locked = bool(move.date >= lock_date)

    @api.multi
    def lock_move(self):
        return self.sudo().write({'locked': True})

    @api.multi
    def unlock_move(self):
        return self.sudo().write({'locked': False})

    @api.multi
    def _check_lock_date(self):
        res = super(AccountMove, self)._check_lock_date()
        if self.env['account.journal']._can_bypass_journal_lock_date():
            return res
        for move in self:
            lock_date = move.journal_id.lock_date
            if lock_date and move.date <= lock_date:
                raise JournalLockDateError(
                    _("You cannot add/modify entries prior to and "
                      "inclusive of the journal lock date %s") %
                    (lock_date, ))
            if move.locked:
                raise JournalLockDateError(
                    _("The move %s has been locked. You need to have "
                      "'Adviser' role.") % move.name)
        return res

    @api.model
    def create(self, vals):
        result = super(AccountMove, self).create(vals)
        result._check_lock_date()
        return result

    @api.multi
    def write(self, vals):
        self._check_lock_date()
        return super(AccountMove, self).write(vals)

    @api.multi
    def unlink(self):
        self._check_lock_date()
        return super(AccountMove, self).unlink()

    @api.multi
    def button_cancel(self):
        self._check_lock_date()
        return super(AccountMove, self).button_cancel()
