# Copyright 2011- Slobodni programi d.o.o.
# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('amount_total')
    def _onchange_amount_total(self):
        for inv in self:
            if inv.journal_id.posting_policy == 'contra' and\
                    inv.amount_total < 0:
                raise UserError(_('You cannot validate an invoice with a '
                                  'negative total amount. You should create '
                                  'a credit note instead.'))

    @api.multi
    def action_invoice_open(self):
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        contra_inv = to_open_invoices.filtered(
            lambda inv: inv.journal_id.posting_policy == 'contra')
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_(
                "Invoice must be in draft state in order to validate it."))
        if contra_inv.filtered(lambda inv: inv.amount_total < 0):
            raise UserError(_(
                "You cannot validate an invoice with a negative total amount. "
                "You should create a credit note instead."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()

    @api.multi
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        for invoice in self:
            if invoice.journal_id.posting_policy == 'storno':
                residual = 0.0
                residual_company_signed = 0.0
                sign = -1 if invoice.type in ['in_refund', 'out_refund'] else 1
                for line in invoice.sudo().move_id.line_ids:
                    if line.account_id == invoice.account_id:
                        residual_company_signed += line.amount_residual
                        if line.currency_id == invoice.currency_id:
                            residual += line.amount_residual_currency if \
                                line.currency_id else line.amount_residual
                        else:
                            from_currency = line.currency_id.with_context(
                                date=line.date) if line.currency_id else\
                                line.company_id.currency_id.with_context(
                                    date=line.date)
                            residual += from_currency.compute(
                                line.amount_residual, invoice.currency_id)
                invoice.residual_company_signed = \
                    residual_company_signed * sign
                invoice.residual_signed = residual * sign
                invoice.residual = residual
                digits_rounding = invoice.currency_id.rounding
                invoice.reconciled = bool(float_is_zero(
                    invoice.residual, precision_rounding=digits_rounding))
            else:
                super(AccountInvoice, invoice)._compute_residual()

    @api.multi
    def _get_outstanding_info_JSON(self):
        self.ensure_one()
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.journal_id.posting_policy == 'storno':
            if self.state == 'open':
                domain = [('account_id', '=', self.account_id.id),
                          ('partner_id', '=',
                           self.env['res.partner']._find_accounting_partner(
                               self.partner_id).id),
                          ('reconciled', '=', False),
                          '|',
                          ('amount_residual', '!=', 0.0),
                          ('amount_residual_currency', '!=', 0.0)]
                if self.type in ('out_invoice', 'in_refund'):
                    if self.amount_total >= 0:
                        domain.extend(
                            ['|',
                             '&', ('credit', '>', 0), ('debit', '=', 0),
                             '&', ('credit', '=', 0), ('debit', '<', 0)])
                    else:
                        domain.extend(
                            ['|',
                             '&', ('credit', '<', 0), ('debit', '=', 0),
                             '&', ('credit', '=', 0), ('debit', '>', 0)])
                    type_payment = _('Outstanding credits')
                else:
                    if self.amount_total >= 0:
                        domain.extend(
                            ['|',
                             '&', ('credit', '<', 0), ('debit', '=', 0),
                             '&', ('credit', '=', 0), ('debit', '>', 0)])
                    else:
                        domain.extend(
                            ['|',
                             '&', ('credit', '>', 0), ('debit', '=', 0),
                             '&', ('credit', '=', 0), ('debit', '<', 0)])
                    type_payment = _('Outstanding debits')
                info = {'title': '', 'outstanding': True,
                        'content': [], 'invoice_id': self.id}
                lines = self.env['account.move.line'].search(domain)
                currency_id = self.currency_id
                if lines:
                    for line in lines:
                        # get the residual value in invoice currency
                        if line.currency_id and \
                                line.currency_id == self.currency_id:
                            amount_to_show = line.amount_residual_currency
                        else:
                            amount_to_show = \
                                line.company_id.currency_id.with_context(
                                    date=line.date).compute(
                                        line.amount_residual, self.currency_id)
                        if float_is_zero(
                                amount_to_show,
                                precision_rounding=self.currency_id.rounding):
                            continue
                        info['content'].append({
                            'journal_name': line.ref or line.move_id.name,
                            'amount': amount_to_show,
                            'currency': currency_id.symbol,
                            'id': line.id,
                            'position': currency_id.position,
                            'digits': [69, self.currency_id.decimal_places],
                        })
                    info['title'] = type_payment
                    self.outstanding_credits_debits_widget = json.dumps(info)
                    self.has_outstanding = True
        else:
            super(AccountInvoice, self)._get_outstanding_info_JSON()

    @api.model
    def _get_payments_vals(self):
        if self.journal_id.posting_policy != 'storno':
            return super(AccountInvoice, self)._get_payments_vals()
        if not self.payment_move_line_ids:
            return []
        payment_vals = []
        currency_id = self.currency_id
        for payment in self.payment_move_line_ids:
            payment_currency_id = False
            amount = sum(
                [p.amount for p in payment.matched_debit_ids
                 if p.debit_move_id in self.move_id.line_ids] +
                [p.amount for p in payment.matched_credit_ids
                 if p.credit_move_id in self.move_id.line_ids])
            amount_currency = sum(
                [p.amount_currency for p in payment.matched_debit_ids
                 if p.debit_move_id in self.move_id.line_ids] +
                [p.amount_currency for p in payment.matched_credit_ids
                 if p.credit_move_id in self.move_id.line_ids])
            if payment.matched_debit_ids:
                payment_currency_id =\
                    payment.matched_debit_ids[0].currency_id if all(
                        [p.currency_id ==
                         payment.matched_debit_ids[0].currency_id
                         for p in payment.matched_debit_ids]) else False
            if payment.matched_credit_ids:
                payment_currency_id =\
                    payment.matched_credit_ids[0].currency_id if all(
                        [p.currency_id ==
                         payment.matched_credit_ids[0].currency_id
                         for p in payment.matched_credit_ids]) else False
            # get the payment value in invoice currency
            if payment_currency_id and payment_currency_id == self.currency_id:
                amount_to_show = amount_currency
            else:
                amount_to_show = payment.company_id.currency_id.with_context(
                    date=self.date).compute(amount, self.currency_id)
            if float_is_zero(amount_to_show,
                             precision_rounding=self.currency_id.rounding):
                continue
            payment_ref = payment.move_id.name
            if payment.move_id.ref:
                payment_ref += ' (' + payment.move_id.ref + ')'
            payment_vals.append({
                'name': payment.name,
                'journal_name': payment.journal_id.name,
                'amount': amount_to_show,
                'currency': currency_id.symbol,
                'digits': [69, currency_id.decimal_places],
                'position': currency_id.position,
                'date': payment.date,
                'payment_id': payment.id,
                'account_payment_id': payment.payment_id.id,
                'invoice_id': payment.invoice_id.id,
                'move_id': payment.move_id.id,
                'ref': payment_ref,
            })
        return payment_vals

    def group_lines(self, iml, line):
        """Merge account move lines (and hence analytic lines) if invoice
           line hashcodes are equals"""
        if self.journal_id.posting_policy == 'storno':
            if self.journal_id.group_invoice_lines:
                line2 = {}
                for index1, index2, convline in line:
                    tmp = self.inv_line_characteristic_hashcode(convline)
                    if tmp in line2:
                        debit = line2[tmp]['debit'] + convline['debit']
                        credit = line2[tmp]['credit'] + convline['credit']
                        line2[tmp]['debit'] = debit
                        line2[tmp]['credit'] = credit
                        line2[tmp]['amount_currency'] += \
                            convline['amount_currency']
                        line2[tmp]['analytic_line_ids'] += \
                            convline['analytic_line_ids']
                        qty = convline.get('quantity')
                        if qty:
                            line2[tmp]['quantity'] = line2[tmp].get(
                                'quantity', 0.0) + qty
                    else:
                        line2[tmp] = convline
                line = []
                for val in line2.values():
                    line.append((0, 0, val))
        else:
            line = super(AccountInvoice, self).group_lines(iml, line)
        return line
