# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp.osv import fields, orm


class account_move(orm.Model):
    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            for line in move.line_id:
                if line.move_line_to_reconcile_id:
                    account_move_line_obj = self.pool.get('account.move.line')
                    account_move_line_obj.reconcile_partial(
                        cr, uid,
                        [line.id, line.move_line_to_reconcile_id.id],
                        context=context
                    )
        return super(account_move, self).post(cr, uid, ids, context=context)


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    _columns = {
        'move_line_to_reconcile_id': fields.many2one(
            'account.move.line',
            'Move Line To Reconcile',
        ),
    }
