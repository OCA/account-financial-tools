# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Camptocamp (http://www.camptocamp.com) 
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

from tools.translate import _
from osv import osv
from openerp.osv.orm import TransientModel

class account_invoice(TransientModel):
    _inherit = "account.invoice"
    
    def action_cancel(self, cr, uid, ids, *args):
        ### 
        invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids'])
        for i in invoices:
            if i['move_id']:
                ## This invoice have a move line, we search move_line converned by this move
                cr.execute("""select (select name from account_bank_statement where id = statement_id) as statement_name, 
                    ((select date from account_bank_statement where id = statement_id)) as statement_date, 
                    name from account_bank_statement_line where voucher_id in 
                    ( select voucher_id from account_voucher_line where move_line_id in (
                    select id from account_move_line where move_id = %s ))""", (i['move_id'][0],))
                statement_lines = cr.dictfetchall()
                if statement_lines:
                    raise osv.except_osv(_('Error !'), 
                                         _('Invoice already import in bank statment (%s) at %s on line %s'
                                            % (statement_lines[0]['statement_name'],
                                               statement_lines[0]['statement_date'],
                                               statement_lines[0]['name'],)))

        
        
        return super(account_invoice,self).action_cancel(cr, uid, ids, *args)
