# -*- coding: utf-8 -*-

import json

from odoo import models, api, _
from odoo.tools import float_is_zero
from odoo.addons.account.models.account_payment import \
    MAP_INVOICE_TYPE_PAYMENT_SIGN


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        super(AccountInvoice, self)._compute_residual()
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:
            if line.account_id.internal_type in ('receivable', 'payable'):
                residual_company_signed += line.amount_residual
                if line.currency_id == self.currency_id:
                    residual += line.amount_residual_currency if \
                        line.currency_id else line.amount_residual
                else:
                    from_currency = (
                        line.currency_id and line.currency_id.with_context(
                            date=line.date)) or line.company_id.currency_id.\
                        with_context(date=line.date)
                    residual += from_currency.compute(
                        line.amount_residual, self.currency_id)
        self.residual_company_signed = residual_company_signed if (
            residual_company_signed < 0 and self.type in [
                'in_invoice', 'out_invoice']) else \
            abs(residual_company_signed) * sign
        self.residual_signed = residual if (
            residual < 0 and self.type in [
                'in_invoice', 'out_invoice']) else abs(residual) * sign
        self.residual = residual if (
            residual < 0 and self.type not in [
                'in_invoice', 'out_invoice']) else abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(
                self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

    @api.one
    def _get_outstanding_info_JSON(self):
        super(AccountInvoice, self)._get_outstanding_info_JSON()
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain = [
                ('account_id', '=', self.account_id.id),
                ('partner_id', '=', self.env[
                    'res.partner']._find_accounting_partner(
                    self.partner_id).id),
                ('reconciled', '=', False),
                ('amount_residual', '!=', 0.0)
            ]
            if self.type in ('out_invoice', 'in_refund'):
                if self.type == 'out_invoice' and self.residual < 0:
                    domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                else:
                    domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
            info = {'title': '', 'outstanding': True, 'content': [],
                    'invoice_id': self.id}
            lines = self.env['account.move.line'].search(domain)
            currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == \
                            self.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        amount_to_show = line.company_id.currency_id.\
                            with_context(date=line.date).compute(abs(
                                line.amount_residual), self.currency_id)
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

    @api.one
    @api.depends('payment_move_line_ids.amount_residual')
    def _get_payment_info_JSON(self):
        res = super(AccountInvoice, self)._get_payment_info_JSON()
        # todo if invoice or refund are negative, get correct payments to show
        if self.amount_untaxed_signed < 0:
            self.payments_widget = json.dumps(False)
            if self.payment_move_line_ids:
                info = {'title': _('Less Payment'),
                        'outstanding': False, 'content': []}
                currency_id = self.currency_id
                for payment in self.payment_move_line_ids:
                    payment_currency_id = False
                    if self.type in ['in_invoice', 'out_refund']:
                        if payment.full_reconcile_id:
                            amount = payment.credit
                            amount_currency = payment.credit
                        else:
                            amount = sum(
                                [p.amount for p in payment.
                                    matched_debit_ids if p.debit_move_id in
                                    self.move_id.line_ids])
                            amount_currency = sum(
                                [p.amount_currency for p in payment.
                                    matched_debit_ids if p.debit_move_id in
                                    self.move_id.line_ids])
                        if payment.matched_debit_ids:
                            payment_currency_id = all(
                                [p.currency_id == payment.matched_debit_ids[
                                    0].currency_id for p in
                                    payment.matched_debit_ids]) and \
                                payment.matched_debit_ids[0].currency_id \
                                or False
                    elif self.type in ['out_invoice', 'in_refund']:
                        if payment.full_reconcile_id:
                            amount = payment.debit  # sum([
                            # p.amount for p in payment.full_reconcile_id.
                            # partial_reconcile_ids if
                            # p.credit_move_id in self.move_id.line_ids])
                            amount_currency = payment.debit  # sum([
                            # p.amount_currency for p in
                            # payment.full_reconcile_id.
                            # partial_reconcile_ids if
                            # p.credit_move_id in
                            # self.move_id.line_ids])
                        else:
                            amount = sum([
                                p.amount for p in
                                payment.matched_credit_ids
                                if p.credit_move_id in self.move_id.line_ids])
                            amount_currency = sum([
                                p.amount_currency for p in
                                payment.matched_credit_ids
                                if p.credit_move_id in self.move_id.line_ids])
                        if payment.matched_credit_ids:
                            payment_currency_id = all([
                                p.currency_id == payment.matched_credit_ids[
                                    0].currency_id for p in
                                payment.matched_credit_ids]) and \
                                payment.matched_credit_ids[0].currency_id\
                                or False
                    # get the payment value in invoice currency
                    if payment_currency_id and payment_currency_id == \
                            self.currency_id:
                        amount_to_show = amount_currency
                    else:
                        amount_to_show = payment.company_id.currency_id.\
                            with_context(date=payment.date).compute(
                                amount, self.currency_id)
                    if float_is_zero(
                            amount_to_show,
                            precision_rounding=self.currency_id.rounding):
                        continue
                    payment_ref = payment.move_id.name
                    if payment.move_id.ref:
                        payment_ref += ' (' + payment.move_id.ref + ')'
                    info['content'].append({
                        'name': payment.name,
                        'journal_name': payment.journal_id.name,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'digits': [69, currency_id.decimal_places],
                        'position': currency_id.position,
                        'date': payment.date,
                        'payment_id': payment.id,
                        'move_id': payment.move_id.id,
                        'ref': payment_ref,
                    })
                self.payments_widget = json.dumps(info)
        return res


class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        return True

    def _compute_total_invoices_amount(self):
        """ Compute the sum of the residual of invoices, expressed in the
        payment currency """
        total = super(account_abstract_payment, self). \
            _compute_total_invoices_amount()
        payment_currency = self.currency_id or self.journal_id.currency_id \
            or self.journal_id.company_id.currency_id \
            or self.env.user.company_id.currency_id
        invoices = self._get_invoices()

        if all(inv.currency_id == payment_currency for inv in invoices):
            total = sum(invoices.mapped('residual_signed'))
        else:
            total = 0
            for inv in invoices:
                if inv.company_currency_id != payment_currency:
                    total += inv.company_currency_id.with_context(
                        date=self.payment_date).compute(
                            inv.residual_company_signed, payment_currency)
                else:
                    total += inv.residual_company_signed
        return total


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.one
    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id')
    def _compute_payment_difference(self):
        res = super(account_payment, self)._compute_payment_difference()
        if self._compute_total_invoices_amount() < 0:
            if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                self.payment_difference = - self.amount + \
                    self._compute_total_invoices_amount()
            else:
                self.payment_difference = self.amount - \
                    self._compute_total_invoices_amount()
        return res

    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands(
            'invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            rec.update({
                'amount': invoice['residual_signed'],
            })
        return rec


class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"

    @api.model
    def default_get(self, fields):
        rec = super(account_register_payments, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        invoices = self.env[active_model].browse(active_ids)
        total_amount = sum(inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[
            inv.type] for inv in invoices)
        rec.update({
            'amount': total_amount,
        })
        return rec
