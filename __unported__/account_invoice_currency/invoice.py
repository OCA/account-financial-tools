# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
#        Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


from openerp.osv import fields
from openerp.osv import orm
import openerp.addons.decimal_precision as dp


class account_invoice(orm.Model):
    """
    Inheritance of account invoice to add company currency amounts
    """

    _inherit = "account.invoice"

    def _get_invoice_line2(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(
                cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax2(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(
                cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def _cc_amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.company_id.currency_id == invoice.currency_id:
                res[invoice.id] = {
                    'cc_amount_untaxed': invoice.amount_untaxed,
                    'cc_amount_tax': invoice.amount_tax,
                    'cc_amount_total': invoice.amount_total,
                }
            else:
                res[invoice.id] = {
                    'cc_amount_untaxed': 0.0,
                    'cc_amount_tax': 0.0,
                    'cc_amount_total': 0.0,
                }

                # It could be computed only in open or paid invoices with a generated account move
                if invoice.move_id:
                    # Accounts to compute amount_untaxed
                    line_account = []
                    for line in invoice.invoice_line:
                        if line.account_id.id not in line_account:
                            line_account.append(line.account_id.id)

                    # Accounts to compute amount_tax
                    tax_account = []
                    for line in invoice.tax_line:
                        if line.account_id.id not in tax_account and line.amount != 0:
                            tax_account.append(line.account_id.id)

                    # The company currency amounts are the debit-credit amounts in the account moves
                    for line in invoice.move_id.line_id:
                        if line.account_id.id in line_account:
                            res[invoice.id]['cc_amount_untaxed'] += line.debit - line.credit
                        if line.account_id.id in tax_account:
                            res[invoice.id]['cc_amount_tax'] += line.debit - line.credit
                    if invoice.type in ('out_invoice', 'in_refund'):
                        res[invoice.id]['cc_amount_untaxed'] = -res[invoice.id]['cc_amount_untaxed']
                        res[invoice.id]['cc_amount_tax'] = -res[invoice.id]['cc_amount_tax']
                    res[invoice.id]['cc_amount_total'] = (res[invoice.id]['cc_amount_tax'] +
                                                          res[invoice.id]['cc_amount_untaxed'])
        return res

    _columns = {
        'cc_amount_untaxed': fields.function(
            _cc_amount_all,
            method=True,
            digits_compute=dp.get_precision('Account'),
            string='Company Cur. Untaxed',
            help="Invoice untaxed amount in the company currency"
                 "(useful when invoice currency is different from company currency).",
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line',
                                                                           'currency_id',
                                                                           'move_id'], 20),
                'account.invoice.tax': (_get_invoice_tax2, None, 20),
                'account.invoice.line': (_get_invoice_line2, ['price_unit',
                                                              'invoice_line_tax_id',
                                                              'quantity', 'discount'], 20),
            },
            multi='cc_all'
        ),

        'cc_amount_tax': fields.function(
            _cc_amount_all,
            method=True,
            digits_compute=dp.get_precision('Account'),
            string='Company Cur. Tax',
            help="Invoice tax amount in the company currency "
                 "(useful when invoice currency is different from company currency).",
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line',
                                                                           'currency_id',
                                                                           'move_id'], 20),
                'account.invoice.tax': (_get_invoice_tax2, None, 20),
                'account.invoice.line': (_get_invoice_line2, ['price_unit',
                                                              'invoice_line_tax_id',
                                                              'quantity', 'discount'], 20),
            },
            multi='cc_all'
        ),

        'cc_amount_total': fields.function(
            _cc_amount_all,
            method=True,
            digits_compute=dp.get_precision('Account'),
            string='Company Cur. Total',
            help="Invoice total amount in the company currency "
            "(useful when invoice currency is different from company currency).",
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line',
                                                                           'currency_id',
                                                                           'move_id'], 20),
                'account.invoice.tax': (_get_invoice_tax2, None, 20),
                'account.invoice.line': (_get_invoice_line2, ['price_unit',
                                                              'invoice_line_tax_id',
                                                              'quantity', 'discount'], 20),
            },
            multi='cc_all'),
    }
