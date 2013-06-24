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

from openerp.osv import osv, orm
from openerp.tools.translate import _

class invoice_merge(orm.TransientModel):
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

    def merge_invoices(self, cr, uid, _ids, context=None):
        """
             To merge similar type of account invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: account invoice view

        """
        invoice_obj = self.pool.get('account.invoice')
        mod_obj =self.pool.get('ir.model.data')
        so_obj = self.pool.get('sale.order')
        po_obj = self.pool.get('purchase.order')

        if context is None:
            context = {}
        try:
            search_view_id = mod_obj.get_object(cr, uid, 'account', 'view_account_invoice_filter').id
        except ValueError:
            search_view_id = False
        allinvoices = invoice_obj.do_merge(cr, uid, context.get('active_ids',[]), context)

        for new_invoice in allinvoices:
            todo_ids = so_obj.search(cr, uid, [('invoice_ids', 'in', allinvoices[new_invoice])], context=context)
            for org_invoice in so_obj.browse(cr, uid, todo_ids, context=context):
                so_obj.write(cr, uid, [org_invoice.id], {'invoice_ids': [(4, new_invoice)]}, context)
            todo_ids = po_obj.search(cr, uid, [('invoice_ids', 'in', allinvoices[new_invoice])], context=context)
            for org_invoice in po_obj.browse(cr, uid, todo_ids, context=context):
                po_obj.write(cr, uid, [org_invoice.id], {'invoice_ids': [(4, new_invoice)]}, context)
        print allinvoices
        return {
            'domain': "[('id', 'in', [%s])]" % ','.join(str(inv_id) for inv_id in allinvoices),
            'name': _('Partner Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            #'view_id': [view_id],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': search_view_id,
            #'target': 'current',
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
