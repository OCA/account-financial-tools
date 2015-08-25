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

from openerp.osv import fields, orm
from tools.translate import _


class lock_account_move(orm.TransientModel):
    _name = "lock.account.move"
    _description = "Lock Account Move"

    _columns = {
        'journal_ids': fields.many2many('account.journal',
                                        rel='wizard_lock_account_move_journal',
                                        string='Journal',
                                        required=True),
        'period_ids': fields.many2many('account.period',
                                       rel='wizard_lock_account_move_period',
                                       string='Period',
                                       required=True,
                                       domain=[('state', '<>', 'done')])
    }

    def lock_move(self, cr, uid, ids, context=None):
        obj_move = self.pool['account.move']
        data = self.browse(cr, uid, ids, context=context)[0]
        journal_ids = [journal.id for journal in data.journal_ids]
        period_ids = [period.id for period in data.period_ids]
        draft_move_ids = obj_move.search(
            cr, uid, [('state', '=', 'draft'),
                      ('journal_id', 'in', journal_ids),
                      ('period_id', 'in', period_ids)],
            order='date',
            limit=1,
            context=context)
        if draft_move_ids:
            raise orm.except_orm(
                _(u'Warning'),
                _('Unposted move in period/jounal \
                   selected, please post it before \
                   locking them'))

        move_ids = obj_move.search(
            cr, uid,
            [('state', '=', 'posted'),
             ('locked', '=', False),
             ('journal_id', 'in', journal_ids),
             ('period_id', 'in', period_ids)],
            order='date',
            context=context)
        if not move_ids:
            raise orm.except_orm(
                _(u'Warning'),
                _('No move to locked found'))
        obj_move.write(cr, uid, move_ids, {'locked': True}, context=context)
        return {'type': 'ir.actions.act_window_close'}
