# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011- Slobodni programi d.o.o.
#    @author: Goran Kliska
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


class account_invoice(orm.Model):
    """Not knowing legal requirements of all storno countries about journals
       This version is for Croatia, Bih, Serbia...
       Candidate for new module?
    """
    _inherit = "account.invoice"

    def _journal_dict(self):
        return {'sale': 'out_invoice',  # Customer Invoice
                'purchase': 'in_invoice',  # Customer Refund
                'sale_refund': 'out_refund',   # Supplier Invoice
                'purchase_refund': 'in_refund'}   # Supplier Refund

    def refund(self, cr, uid, ids, date=None, period_id=None,
               description=None, journal_id=None, context=None):
        # Where is the context, per invoice method?
        # This approach is slow, updating after creating,
        # but maybe better than copy-paste whole method
        res = super(account_invoice, self).refund(cr, uid, ids, date=date,
                                                  period_id=period_id,
                                                  description=description,
                                                  journal_id=journal_id,
                                                  context=context)
        for invoice in self.pool['account.invoice'].browse(cr, uid, res):
            self.pool['account.invoice'].write(
                cr, uid, [invoice.id],
                {'type': self._journal_dict()[invoice.journal_id.type]},
                context=context)
            if invoice.journal_id.posting_policy == 'storno':
                for inv_line in invoice.invoice_line:
                    self.pool['account.invoice.line'].write(
                        cr, uid, [inv_line.id],
                        {'quantity': inv_line.quantity * (-1)},
                        context=context)
                for tax_line in invoice.tax_line:
                    if tax_line.manual or True:
                        self.pool['account.invoice.tax'].write(
                            cr, uid, [tax_line.id],
                            {'base': tax_line.base * (-1),
                             'amount': tax_line.amount * (-1),
                             'base_amount': tax_line.base_amount * (-1),
                             'tax_amount': tax_line.tax_amount * (-1)},
                            context=context)
        return res


class account_invoice_refund(orm.TransientModel):
    _inherit = "account.invoice.refund"

    def _get_journal(self, cr, uid, context=None):
        """"in Croatia, Romania for out invoice refunds must go to same journal
            TODO for localization ???
        """
        # Borrowed from Akretion account_journal_sale_refund_link
        # Compatibility with crm_claim_rma module
        invoice_id = context.get('invoice_ids', [context['active_id']])[0]
        invoice = self.pool['account.invoice'].browse(cr, uid,
                                                      invoice_id,
                                                      context=context)
        refund_journal_id = invoice.journal_id.refund_journal_id
        if refund_journal_id:
            return refund_journal_id.id
        elif invoice.journal_id.posting_policy == 'storno':
            return False  # meaning: same journal as original
        else:
            return super(account_invoice_refund, self)._get_journal(cr,
                                                                    uid,
                                                                    context)

    _defaults = {
        'journal_id': _get_journal,
        }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):
        journal_obj = self.pool['account.journal']
        user_obj = self.pool['res.users']
        res = super(account_invoice_refund, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type,
            context=context, toolbar=toolbar, submenu=submenu)
        company_id = user_obj.browse(cr, uid,
                                     uid, context=context).company_id.id
        # I would love to have invoice.journal_id.posting_policy here
        invoice_type = context.get('type', 'all')
        if invoice_type in ('out_invoice', 'out_refund'):
            journal_types = ('sale', 'sale_refund')
        elif invoice_type in ('in_invoice', 'in_refund'):
            journal_types = ('purchase', 'purchase_refund')
        else:
            journal_types = ('sale', 'sale_refund',
                             'purchase', 'purchase_refund')
        journal_select = journal_obj._name_search(
            cr, uid, '',
            [('type', 'in', journal_types),
             ('company_id', 'child_of', [company_id])],
            context=context)
        for field in res['fields']:
            if field == 'journal_id':
                res['fields'][field]['selection'] = journal_select
        return res

    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        mod_obj = self.pool['ir.model.data']
        act_obj = self.pool['ir.actions.act_window']
        if context is None:
            context = {}
        res = super(account_invoice_refund, self).compute_refund(
            cr, uid, ids, mode=mode, context=context)
        # yupiii here is last created invoice id, great hook
        last_inv_id = res['domain'][1][2][-1]
        inv = self.pool['account.invoice'].browse(cr, uid, [last_inv_id])[0]
        xml_id = (inv.type == 'out_refund') and 'action_invoice_tree3' or \
                 (inv.type == 'in_refund') and 'action_invoice_tree4' or \
                 (inv.type == 'out_invoice') and 'action_invoice_tree1' or \
                 (inv.type == 'in_invoice') and 'action_invoice_tree2'
        result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        invoice_domain = eval(result['domain'])
        invoice_domain.append(('id', 'in', res['domain'][1][2]))
        result['domain'] = invoice_domain
        return result
