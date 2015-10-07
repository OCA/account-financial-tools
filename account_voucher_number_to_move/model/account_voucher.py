# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Eficent (<http://www.eficent.com/>)
#              <contact@eficent.com>
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
from openerp.osv import fields, orm


class AccountVoucher(orm.Model):

    _inherit = 'account.voucher'

    def write(self, cr, uid, ids, vals, context=None):
        move_obj = self.pool['account.move']
        move_line_obj = self.pool['account.move.line']
        for voucher in self.browse(cr, uid, ids, context=context):
            if vals.get('number') and voucher.move_id:
                if vals['number']:
                    move_obj.write(cr, uid, [voucher.move_id.id],
                                   {'ref': vals.get('number')},
                                   context=context)
                    move_line_ids = []
                    name = vals.get('number')
                    for move_line in voucher.move_id.line_id:
                        move_line_ids.append(move_line.id)
                    move_line_obj.write(cr, uid, move_line_ids,
                                        {'ref': name},
                                        context=context)
        return super(AccountVoucher, self).write(cr, uid, ids, vals,
                                                 context=context)
