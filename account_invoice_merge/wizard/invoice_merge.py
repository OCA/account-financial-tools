# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Erico-Corp (<http://www.openerp.net.cn>).
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
import time

from osv import fields, osv
import netsvc
import pooler
from osv.orm import browse_record, browse_null
from tools.translate import _

class invoice_merge(osv.osv_memory):
    _name = "invoice.merge"
    _description = "Merge Partner Invoice"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        if context is None:
            context={}
        res = super(invoice_merge, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)

        if context.get('active_model','') == 'account.invoice' and len(context['active_ids']) < 2:
            raise osv.except_osv(_('Warning'),
            _('Please select multiple invoice to merge in the list view.'))
        return res

    def merge_invoices(self, cr, uid, ids, context=None):
        """
             To merge similar type of account invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: account invoice view

        """
        order_obj = self.pool.get('account.invoice')
        mod_obj =self.pool.get('ir.model.data')
        so_obj = self.pool.get('sale.order')
        po_obj = self.pool.get('purchase.order')

        if context is None:
            context = {}
        result = mod_obj._get_id(cr, uid, 'account', 'invoice_form')

        allorders = order_obj.do_merge(cr, uid, context.get('active_ids',[]), context)

        for new_order in allorders:
            todo_ids = []
            todo_ids += so_obj.search(cr, uid, [('invoice_ids', 'in', allorders[new_order])], context=context)
            for org_order in so_obj.browse(cr, uid, todo_ids, context=context):
                so_obj.write(cr, uid, [org_order.id], {'invoice_ids': [(4, new_order)]}, context)
            todo_ids += po_obj.search(cr, uid, [('invoice_ids', 'in', allorders[new_order])], context=context)
            for org_order in po_obj.browse(cr, uid, todo_ids, context=context):
                po_obj.write(cr, uid, [org_order.id], {'invoice_ids': [(4, new_order)]}, context)

        return {
            'domain': "[('id','in', [" + ','.join(map(str, allorders.keys())) + "])]",
            'name': _('Partner Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': [result or False],
            #'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            #'nodestroy': True,
            'target': 'current',
            #'res_id': inv_ids and inv_ids[0] or False,
        }

invoice_merge()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
