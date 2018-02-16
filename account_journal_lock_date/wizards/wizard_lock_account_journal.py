# Copyright 2017 ACSONE SA/NV
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _, SUPERUSER_ID

from ..exceptions import JournalLockDateError


class WizardLockAccountJournal(models.TransientModel):
    _name = "wizard.lock.account.journal"
    _description = "Lock Account Journal"

    company_id = fields.Many2one(
        comodel_name='res.company', string="Company", required=True,
        default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many(
        'account.journal', rel='wizard_lock_account_move_journal',
        string='Journals', required=True)
    lock_date = fields.Date(string='Lock Date', required=True)
    permanent_lock = fields.Boolean('Permanent Lock')

    @api.multi
    def _check_execute_allowed(self):
        self.ensure_one()
        obj_move = self.env['account.move']
        has_adviser_group = self.env.user.has_group(
            'account.group_account_manager')
        if not (has_adviser_group or self.env.uid == SUPERUSER_ID):
            raise JournalLockDateError(
                _("You are not allowed to execute this action."))
        fy_lock_date = self.company_id.fiscalyear_lock_date
        if fy_lock_date and self.lock_date < fy_lock_date:
            raise JournalLockDateError(
                _("You cannot choose a lock date lower than company "
                  "fiscalyear lock date %s.") % fy_lock_date)
        draft_move = obj_move.search(
            [('state', '=', 'draft'),
             ('journal_id', 'in', self.journal_ids.ids),
             ('date', '<=', self.lock_date)],
            order='date')
        if draft_move:
            raise JournalLockDateError(
                _("Unposted move in period/jounal selected, "
                  "please post it before locking them"))

    @api.multi
    def lock_moves(self):
        obj_move = self.env['account.move']
        # Lock moves with date lower than lock_date.
        to_lock_moves = obj_move.search(
            [('state', '=', 'posted'),
             ('locked', '=', False),
             ('journal_id', 'in', self.journal_ids.ids),
             ('date', '<=', self.lock_date)],
            order='date')
        to_lock_moves.lock_move()
        # Unlock moves with date bigger than lock_date.
        to_unlock_moves = obj_move.search(
            [('state', '=', 'posted'),
             ('locked', '=', True),
             ('journal_id', 'in', self.journal_ids.ids),
             ('date', '>', self.lock_date)],
            order='date')
        to_unlock_moves.unlock_move()
        self.journal_ids.write({'lock_date': self.lock_date,
                                'permanent_lock': self.permanent_lock})
        # Write journals lock date
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def execute(self):
        self.ensure_one()
        self._check_execute_allowed()
        self.lock_moves()
