# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville.
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from openerp import fields, models, api, _, exceptions


class lock_account_move(models.TransientModel):
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
