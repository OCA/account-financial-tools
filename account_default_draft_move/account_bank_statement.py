# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2012 Camptocamp SA
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


class AccountBankStatement(orm.Model):
    _inherit = "account.bank.statement"

    def create_move_from_st_line(self, cr, uid, st_line_id, company_currency_id, 
            st_line_number, context=None):
        move_ids = super(AccountBankStatement,self).create_move_from_st_line(cr, uid, st_line_id,
                                                                          company_currency_id,
                                                                          st_line_number, context)
        ## We receive the move created for the bank statement, we set it to draft
        if move_ids:
            move_obj = self.pool.get('account.move')
            move_obj.write(cr, uid, move_ids, {'state': 'draft'}, context=context)
        return move_ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: