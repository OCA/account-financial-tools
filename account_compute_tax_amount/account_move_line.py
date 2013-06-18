# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Camptocamp (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Vincent Renaville (Camptocamp)
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

from openerp.tools.translate import _
from openerp.osv import osv, orm, fields
import openerp.addons.decimal_precision as dp

class account_move_line(orm.TransientModel):
    _inherit = "account.move.line"

    def create(self, cr, uid, vals, context=None, check=True):
        result = super(account_move_line, self).create(cr, uid, vals,
                                                       context=context,
                                                       check=check)
        if result:
            move_line = self.read(cr, uid, result,
                                  ['credit', 'debit', 'tax_code_id'],
                                  context=context)
            if move_line['tax_code_id']:
                tax_amount = move_line['credit'] - move_line['debit']
                self.write(cr, uid, [result],
                           {'tax_amount': tax_amount},
                           context=context)
        return result

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(account_move_line,self).write(cr, uid, ids, vals,
                                                     context=context,
                                                     check=check,
                                                     update_check=update_check)
        if result:
            if ('debit' in vals) or ('credit' in vals):
                move_lines = self.read(cr, uid, ids,
                                       ['credit', 'debit', 'tax_code_id'],
                                       context=context)
                for move_line in move_lines:
                    if move_line['tax_code_id']:
                        tax_amount = move_line['credit'] - move_line['debit']
                        self.write(cr, uid,
                                   [move_line['id']],
                                   {'tax_amount': tax_amount},
                                   context=context)

        return result

    # We set the tax_amount invisible, because we recompute it in every case.
    _columns = {
        'tax_amount': fields.float('Tax/Base Amount', digits_compute=dp.get_precision('Account'),
                                   invisible=True,
                                   select=True,
                                   help=("If the Tax account is a tax code account, "
                                         "this field will contain the taxed amount. "
                                         "If the tax account is base tax code, "
                                         "this field will contain the basic amount (without tax)."),
    }
