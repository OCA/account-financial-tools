# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinancialPayreceive(models.TransientModel):

    _name = 'financial.pay_receive'
    _inherit = ['account.abstract.payment']

    payment_type = fields.Selection(
        required=False,
    )
    payment_method_id = fields.Many2one(
        required=False,
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
            res['amount'] = fm.amount
            res['company_id'] = fm.company_id.id
        return res

    @api.multi
    def doit(self):
        for wizard in self:
            active_id = self._context['active_id']
            account_financial = self.env['financial.move']

            financial_to_pay = account_financial.browse(active_id)

            if financial_to_pay.financial_type == 'p':
                financial_type = 'pp'
            else:
                financial_type = 'rr'

            vals = account_financial._prepare_payment(
                journal_id=wizard.journal_id.id,
                company_id=wizard.company_id.id,
                currency_id=wizard.currency_id.id,
                financial_type=financial_type,
                partner_id=financial_to_pay.partner_id.id,
                document_number=financial_to_pay.document_number,
                date_issue=wizard.date_payment,
                document_item=financial_to_pay.document_item,
                date_maturity=financial_to_pay.date_maturity,
                amount=wizard.amount,
            )

            vals['financial_payment_id'] = active_id
            account_financial.create(vals)
