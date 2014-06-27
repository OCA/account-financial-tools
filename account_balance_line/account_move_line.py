# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Vincent Renaville (Camptocamp)
#    Copyright 2010-2014 Camptocamp SA
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
from openerp.osv import orm, fields


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    def _line_balance(self, cr, uid, ids, field, arg, context=None):
        res = {}
        move_lines = self.read(cr, uid, ids,
                               ['debit', 'credit'],
                               context=context)

        for line in move_lines:
            res[line['id']] = line['debit'] - line['credit']
        return res

    _columns = {
        'line_balance': fields.function(
            _line_balance, method=True,
            string='Balance',
            store=True),
    }
