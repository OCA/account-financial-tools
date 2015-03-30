# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011- Slobodni programi d.o.o., Zagreb
#    Author: Goran Kliska
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
from tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID


class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines
           We have to go one by one to inject invoice to line_get_convert
        """
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            # Update context to have acces to invoice
            context.update({'brw_invoice': inv})
            super(account_invoice, self).action_move_create(cr,
                                                            uid,
                                                            [inv.id],
                                                            context=context)
        return True

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        # Inherit function to move the negative amounts to the correct position
        res = super(account_invoice, self).line_get_convert(cr,
                                                            uid,
                                                            x,
                                                            part,
                                                            date,
                                                            context=context)
        if context is None:
            context = {}
        invoice = context.get('brw_invoice', False)
        if invoice and invoice.journal_id.posting_policy == 'storno':
            credit = debit = 0.0
            if invoice.type in ('out_invoice', 'out_refund'):
                if x.get('type', 'src') in ('dest'):
                    # total amount should to debit
                    debit = x['price']  
                else:
					# Invoice Lines and taxes should be on credit
                    credit = x['price'] * (-1)
            else:
                if x.get('type', 'src') in ('dest'):
                    # total amount should to credit
                    credit = x['price'] * (-1)
                else:
                    # Invoice Lines and taxes should be on debit
                    debit = x['price']
            res['debit'] = debit
            res['credit'] = credit
        return res
        
    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        """ Function of the field residual. It computes the residual amount
            (balance) for each invoice. """
        result = super(account_invoice, self)._amount_residual(cr,
                                                               uid,
                                                               ids,
                                                               name,
                                                               args,
                                                               context=context)
        if context is None:
            context = {}
        ctx = context.copy()
        currency_obj = self.pool.get('res.currency')
        for invoice in self.browse(cr, SUPERUSER_ID, ids, context=context):
            # TO DO
            # Add constrain for contra journal and invoices with
            # total amount negative
            if invoice.journal_id.posting_policy == 'storno':
                nb_inv_in_partial_rec = max_invoice_id = 0
                result[invoice.id] = 0.0
                if invoice.move_id:
                    for aml in invoice.move_id.line_id:
                        if aml.account_id.id == invoice.account_id.id:
                            if aml.currency_id and \
                                aml.currency_id.id == invoice.currency_id.id:
                                result[invoice.id] += \
                                    aml.amount_residual_currency
                            else:
                                ctx['date'] = aml.date
                                result[invoice.id] += currency_obj.compute(
                                    cr,
                                    uid,
                                    aml.company_id.currency_id.id,
                                    invoice.currency_id.id,
                                    aml.amount_residual,
                                    context=ctx)

                            if aml.reconcile_partial_id.line_partial_ids:
                                #we check if the invoice is partially
                                #reconciled and if there are other invoices
                                #involved in this partial reconciliation
                                #(and we sum these invoices)
                                for line in \
                                    aml.reconcile_partial_id.line_partial_ids:
                                    if line.invoice and  \
                                        invoice.type == line.invoice.type:
                                        nb_inv_in_partial_rec += 1
                                        #store the max invoice id as for this
                                        #invoice we will make a balance instead
                                        #of a simple division
                                        max_invoice_id = max(max_invoice_id,
                                                             line.invoice.id)
                if nb_inv_in_partial_rec:
                    #if there are several invoices in a partial reconciliation,
                    #we split the residual by the number of invoice to have a
                    #sum of residual amounts that matches the partner balance
                    new_value = currency_obj.round(cr, uid,
                                                   invoice.currency_id,
                                                   result[invoice.id] / \
                                                   nb_inv_in_partial_rec)
                    if invoice.id == max_invoice_id:
                        #if it's the last the invoice of the bunch of invoices
                        #partially reconciled together, we make a
                        #balance to avoid rounding errors
                        result[invoice.id] = result[invoice.id] - \
                                             ((nb_inv_in_partial_rec - 1) * \
                                             new_value)
                    else:
                        result[invoice.id] = new_value

                #prevent the residual amount on the invoice to be less than 0
                result[invoice.id] = result[invoice.id]            
        return result
        
    def _get_invoice_line(self, cr, uid, ids, context=None):
        # Rewrite residual store function since super is raising error
        result = {}
        for line in self.pool.get('account.invoice.line').browse(
                         cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        # Rewrite residual store function since super is raising error
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(
                         cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def _get_invoice_from_line(self, cr, uid, ids, context=None):
        # Rewrite residual store function since super is raising error
        move = {}
        for line in self.pool.get('account.move.line').browse(
                         cr, uid, ids, context=context):
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    move[line2.move_id.id] = True
            if line.reconcile_id:
                for line2 in line.reconcile_id.line_id:
                    move[line2.move_id.id] = True
        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(
                cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids

    def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
        # Rewrite residual store function since super is raising error
        move = {}
        for r in self.pool.get('account.move.reconcile').browse(
                         cr, uid, ids, context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True

        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(
                cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids

    
    _columns = {
        'residual': fields.function(_amount_residual,
            digits_compute=dp.get_precision('Account'), string='Balance',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids,
                                    ['invoice_line','move_id'], 50),
                'account.invoice.tax': (_get_invoice_tax, None, 50),
                'account.invoice.line': (_get_invoice_line,
                                         ['price_unit',
                                          'invoice_line_tax_id',
                                          'quantity',
                                          'discount',
                                          'invoice_id'],
                                         50),
                'account.move.line': (_get_invoice_from_line, None, 50),
                'account.move.reconcile': (_get_invoice_from_reconcile,
                                           None,
                                           50),
            },
            help="Remaining amount due."),
        }
