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

from osv import fields, osv
import netsvc
from tools.translate import _
from osv.orm import browse_record, browse_null

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def do_merge(self, cr, uid, ids, context=None):
        """
        To merge similar type of account invoices.
        Invoices will only be merged if:
        * Account invoices are in draft
        * Account invoices belong to the same partner
        * Account invoices are have same company, partner, address, currency, journal, currency, salesman, account, type
        Lines will only be merged if:
        * Invoice lines are exactly the same except for the quantity and unit

         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: the ID or list of IDs
         @param context: A standard dictionary

         @return: new account invoice id

        """
        wf_service = netsvc.LocalService("workflow")
        def make_key(br, fields):
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('product_id', 'account_id'):
                    if not field_val:
                        field_val = False
                if isinstance(field_val, browse_record):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif isinstance(field_val, list):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

    # compute what the new orders should contain

        new_orders = {}

        for porder in [order for order in self.browse(cr, uid, ids, context=context) if order.state == 'draft']:
            order_key = make_key(porder, ('partner_id', 'user_id', 'type', 'account_id', 'currency_id', 'journal_id', 'company_id'))
            new_order = new_orders.setdefault(order_key, ({}, []))
            new_order[1].append(porder.id)
            order_infos = new_order[0]
            if not order_infos:
                order_infos.update({
                    'origin': '%s' % (porder.origin or '',),
                    'partner_id': porder.partner_id.id,
                    'address_contact_id': porder.address_contact_id.id,
                    'address_invoice_id': porder.address_invoice_id.id,
                    'journal_id': porder.journal_id.id,
                    'user_id': porder.user_id.id,
                    'currency_id': porder.currency_id.id,
                    'company_id': porder.company_id.id,
                    'type': porder.type,
                    'account_id': porder.account_id.id,
                    'state': 'draft',
                    'invoice_line': {},
                    'reference': '%s' % (porder.reference or '',),
                    'name': '%s' % (porder.name or '',),
                    'fiscal_position': porder.fiscal_position and porder.fiscal_position.id or False,
                    'period_id': porder.period_id and porder.period_id.id or False,
                })
            else:
                if porder.name:
                    order_infos['name'] = (order_infos['name'] or '') + (' %s' % (porder.name,))
                if porder.origin:
                    order_infos['origin'] = (order_infos['origin'] or '') + ' ' + porder.origin
                if porder.reference:
                    order_infos['reference'] = (order_infos['reference'] or '') + (' %s' % (porder.reference,))

            for order_line in porder.invoice_line:
                line_key = make_key(order_line, ('name', 'origin', 'discount', 'invoice_line_tax_id', 'price_unit', 'quantity', 'product_id', 'account_id', 'account_analytic_id'))
                o_line = order_infos['invoice_line'].setdefault(line_key, {})
                if o_line:
                    # merge the line with an existing line
                    o_line['quantity'] += order_line.quantity
                else:
                    # append a new "standalone" line
                    for field in ('quantity', 'uos_id'):
                        field_val = getattr(order_line, field)
                        if isinstance(field_val, browse_record):
                            field_val = field_val.id
                        o_line[field] = field_val

        allorders = []
        orders_info = {}
        for order_key, (order_data, old_ids) in new_orders.iteritems():
            # skip merges with only one order
            if len(old_ids) < 2:
                allorders += (old_ids or [])
                continue

            # cleanup order line data
            for key, value in order_data['invoice_line'].iteritems():
                #del value['uom_factor']
                value.update(dict(key))
            order_data['invoice_line'] = [(0, 0, value) for value in order_data['invoice_line'].itervalues()]

            # create the new order
            neworder_id = self.create(cr, uid, order_data)
            orders_info.update({neworder_id: old_ids})
            allorders.append(neworder_id)

            # make triggers pointing to the old orders point to the new order
            for old_id in old_ids:
                wf_service.trg_redirect(uid, 'account.invoice', old_id, neworder_id, cr)
                wf_service.trg_validate(uid, 'account.invoice', old_id, 'invoice_cancel', cr)
        #print orders_info
        return orders_info

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

