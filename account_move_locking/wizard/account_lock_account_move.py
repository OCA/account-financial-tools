# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _, exceptions


class LockAccountMove(models.TransientModel):
    _name = "lock.account.move"
    _description = "Lock Account Move"

    journal_ids = fields.Many2many('account.journal',
                                   rel='wizard_lock_account_move_journal',
                                   string='Journal',
                                   required=True)
    date_start = fields.Datetime(string='Date start',
                                 required=True)
    date_end = fields.Datetime(string='Date end',
                               required=True)

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_date_stop_start(self):
        if self.date_start > self.date_end:
            raise exceptions.UserError(_('Date start need to be \
                                          before Date end'))

    @api.multi
    def lock_move(self, data):
        obj_move = self.env['account.move']
        draft_move = obj_move.search([('state', '=', 'draft'),
                                      ('journal_id',
                                       'in',
                                       self.journal_ids.ids),
                                      ('date', '>=',
                                       self.date_start),
                                      ('date', '<=',
                                       self.date_end)],
                                     order='date')
        if draft_move:
            raise exceptions.UserError(_('Unposted move in period/jounal \
                                          selected, please post it before \
                                          locking them'))
        move = obj_move.search([('state', '=', 'posted'),
                                ('locked', '=', False),
                                ('journal_id', 'in', self.journal_ids.ids),
                                ('date', '>=', self.date_start),
                                ('date', '<=', self.date_end)],
                               order='date')
        if not move:
            raise exceptions.UserError(_('No move to locked found'))
        move.write({'locked': True})
        return {'type': 'ir.actions.act_window_close'}
