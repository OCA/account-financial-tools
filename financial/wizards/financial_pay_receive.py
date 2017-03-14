# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from ..models.financial_move import (
    FINANCIAL_IN_OUT,
)


class FinancialPayreceive(models.TransientModel):

    _name = 'financial.pay_receive'
    _inherit = ['account.abstract.payment']

    @api.multi
    @api.depends('financial_type')
    def _compute_payment_type(self):
        for record in self:
            if record.financial_type in ('r', 'rr'):
                record.payment_type = 'inbound'
            elif record.financial_type in ('p', 'pp'):
                record.payment_type = 'outbound'

    financial_type = fields.Selection(
        selection=FINANCIAL_IN_OUT,
        required=True,
    )
    amount_paid = fields.Monetary(
        required=True
    )
    ref = fields.Char()
    date_payment = fields.Date(
        required=True,
        default=fields.Date.context_today
    )
    date_credit_debit = fields.Date(
        readonly=True,
        # TODO: compute bussiness date
    )
    amount_discount = fields.Monetary(
        string=u'Discount',
    )
    amount_interest = fields.Monetary(
        string=u'Interest',
        readonly=True,
    )

    @api.model
    def default_get(self, vals):
        res = super(FinancialPayreceive, self).default_get(vals)
        active_id = self.env.context.get('active_id')
        if (self.env.context.get('active_model') == 'financial.move' and
                active_id):
            fm = self.env['financial.move'].browse(active_id)
            res['currency_id'] = fm.currency_id.id
            res['ammount_paid'] = fm.amount_residual
            res['company_id'] = fm.company_id.id
        return res

    @api.multi
    def doit(self):
        for wizard in self:
            active_id = self._context['active_id']
            account_financial = self.env['financial.move']

            financial_to_pay = account_financial.browse(active_id)

            if financial_to_pay.move_type == 'p':
                payment_type = 'pp'
            else:
                payment_type = 'rr'

            account_financial.create({
                'journal_id': wizard.journal_id.id,
                'company_id': wizard.company_id.id,
                'amount_document': wizard.ammount_paid,
                'ref': financial_to_pay.ref,
                'ref_item': financial_to_pay.ref_item,
                'date_credit_debit': wizard.date_credit_debit,
                'payment_method_id': wizard.payment_method_id.id,
                'amount_discount': wizard.amount_discount,
                'amount_interest': wizard.amount_interest,
                'currency_id': wizard.currency_id.id,
                'date_payment': wizard.date_payment,
                'payment_id': active_id,
                'move_type': payment_type,
                'partner_id': financial_to_pay.partner_id.id,
                'document_number': financial_to_pay.document_number,
                'date_maturity': financial_to_pay.date_maturity,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
