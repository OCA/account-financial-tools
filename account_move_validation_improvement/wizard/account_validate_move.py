# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
#
##############################################################################
from openerp.osv import fields, orm, osv
from openerp.tools.translate import _


class ValidateAccountMove(orm.TransientModel):
    _name = "validate.account.move"
    _inherit = "validate.account.move"

    _columns = {
        'journal_ids': fields.many2many('account.journal', string='Journals',
                                        required=True),
        'period_ids': fields.many2many('account.period', string='Periods',
                                       required=True,
                                       domain=[('state', '<>', 'done')]),
        # re-define existing fields as non-mandatory
        'journal_id': fields.many2one('account.journal', 'Journal',
                                      required=False),
        'period_id': fields.many2one('account.period', 'Period',
                                     required=False),
    }

    def validate_move(self, cr, uid, ids, context=None):
        obj_move = self.pool.get('account.move')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        journal_ids = [journal.id for journal in data.journal_ids]
        period_ids = [period.id for period in data.period_ids]
        ids_move = obj_move.search(cr, uid, [('state', '=', 'draft'),
                                             ('journal_id', 'in', journal_ids),
                                             ('period_id', '=', period_ids)],
                                   order='date',
                                   context=context)
        if not ids_move:
            raise osv.except_osv(
                _('Warning!'),
                _('Specified journal does not have any account move entries '
                  'in draft state for this period.')
            )
        obj_move.button_validate(cr, uid, ids_move, context=context)
        return {'type': 'ir.actions.act_window_close'}
