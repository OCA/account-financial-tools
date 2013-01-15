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
from openerp.osv.orm import TransientModel, fields

class account_invoice(TransientModel):
    _inherit = "account.invoice"
    
    def action_cancel(self, cr, uid, ids, *args):
        ### 
        invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids'])
        for invoice in invoices:
            if invoice['move_id']:
                ## This invoice have a move line, we search move_line converned by this move
                cr.execute("""select (select reference from payment_order where id = order_id) as payment_name,
                                (select date_done from payment_order where id = order_id) as payment_date,
                                name from payment_line
                                where move_line_id in (select id from account_move_line where move_id = %s)""",
                                (invoice['move_id'][0],))
                payment_orders = cr.dictfetchall()
                if payment_orders:
                    raise osv.except_osv(_('Error !'), _('''Invoice already import in payment \
                                            order (%s) at %s on line %s''' % 
                                            (payment_orders[0]['payment_name'],
                                             payment_orders[0]['payment_date'],
                                             payment_orders[0]['name'],)))
        return super(account_invoice,self).action_cancel(cr, uid, ids, *args)
    
