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

from openerp.osv import orm
from openerp import netsvc
from osv.orm import browse_record, browse_null

class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def _get_first_invoice_fields(self, cr, uid, invoice):
        return {'origin': '%s' % (invoice.origin or '',),
                'partner_id': invoice.partner_id.id,
                'commercial_partner_id': invoice.commercial_partner_id.id,
                'journal_id': invoice.journal_id.id,
                'user_id': invoice.user_id.id,
                'currency_id': invoice.currency_id.id,
                'company_id': invoice.company_id.id,
                'type': invoice.type,
                'account_id': invoice.account_id.id,
                'state': 'draft',
                'reference': '%s' % (invoice.reference or '',),
                'name': '%s' % (invoice.name or '',),
                'fiscal_position': invoice.fiscal_position and invoice.fiscal_position.id or False,
                'payment_term': invoice.payment_term and invoice.payment_term.id or False,
                'period_id': invoice.period_id and invoice.period_id.id or False,
                'invoice_line': [],
                }

    def _get_invoice_key_cols(self, cr, uid, invoice):
        return ('partner_id', 'commercial_partner_id',
                'user_id', 'type',
                'account_id', 'currency_id',
                'journal_id', 'company_id')

    def _get_invoice_line_key_cols(self, cr, uid, invoice_line):
        return ('name', 'origin', 'discount',
                'invoice_line_tax_id', 'price_unit',
                'product_id', 'account_id', 'quantity',
                'account_analytic_id')

    def do_merge(self, cr, uid, ids, context=None):
        """
        To merge similar type of account invoices.
        Invoices will only be merged if:
        * Account invoices are in draft
        * Account invoices belong to the same partner
        * Account invoices are have same company, partner, currency, journal, currency, salesman, account, type
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

        # compute what the new invoices should contain
        new_invoices = {}
        draft_invoices = [invoice
                          for invoice in self.browse(cr, uid, ids, context=context)
                          if invoice.state == 'draft']
        seen_origins = {}
        seen_client_refs = {}
        for invoice in draft_invoices:
            invoice_key = make_key(invoice, self._get_invoice_key_cols(cr, uid, invoice))
            new_invoice = new_invoices.setdefault(invoice_key, ({}, []))
            origins = seen_origins.setdefault(invoice_key, set())
            client_refs = seen_client_refs.setdefault(invoice_key, set())
            new_invoice[1].append(invoice.id)
            invoice_infos = new_invoice[0]
            if not invoice_infos:
                invoice_infos.update(self._get_first_invoice_fields(cr, uid, invoice))
                origins.add(invoice.origin)
                client_refs.add(invoice.reference)
            else:
                if invoice.name:
                    invoice_infos['name'] = (invoice_infos['name'] or '') + (' %s' % (invoice.name,))
                if invoice.origin and invoice.origin not in origins:
                    invoice_infos['origin'] = (invoice_infos['origin'] or '') + ' ' + invoice.origin
                    origins.add(invoice.origin)
                if invoice.reference and invoice.reference not in client_refs:
                    invoice_infos['reference'] = (invoice_infos['reference'] or '') + (' %s' % (invoice.reference,))
                    client_refs.add(invoice.reference)
            for inv_line in invoice.invoice_line:
                line_key = make_key(inv_line, self._get_invoice_line_key_cols(cr, uid, inv_line))
                line_key = list(line_key)
                if inv_line.uos_id:
                    line_key.append(('uos_id', inv_line.uos_id.id))
                invoice_infos['invoice_line'].append((0, 0, dict(line_key)))

        allinvoices = []
        invoices_info = {}
        for invoice_key, (invoice_data, old_ids) in new_invoices.iteritems():
            # skip merges with only one invoice
            if len(old_ids) < 2:
                allinvoices += (old_ids or [])
                continue

            # create the new invoice
            newinvoice_id = self.create(cr, uid, invoice_data)
            invoices_info.update({newinvoice_id: old_ids})
            allinvoices.append(newinvoice_id)

            # make triggers pointing to the old invoices point to the new invoice
            for old_id in old_ids:
                wf_service.trg_redirect(uid, 'account.invoice', old_id, newinvoice_id, cr)
                wf_service.trg_validate(uid, 'account.invoice', old_id, 'invoice_cancel', cr)

        return invoices_info


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

