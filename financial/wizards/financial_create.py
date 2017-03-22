# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..models.financial_move import (
    FINANCIAL_MOVE,
)


class FinancialMoveCreate(models.TransientModel):

    _name = 'financial.move.create'
    _inherit = ['account.abstract.payment']

    @api.depends('amount', 'amount_discount')
    def _compute_totals(self):
        for record in self:
            record.amount_total = record.amount - record.amount_discount

    payment_type = fields.Selection(
        required=False,
    )
    payment_method_id = fields.Many2one(
        required=False,
    )
    line_ids = fields.One2many(
        comodel_name='financial.move.line.create',
        inverse_name='financial_move_id',
        # readonly=True,
    )
    financial_type = fields.Selection(
        selection=FINANCIAL_MOVE,
        required=True,
    )
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode', string="Payment Mode",
        ondelete='restrict',
    )
    payment_term_id = fields.Many2one(
        string='Payment Term',
        comodel_name='account.payment.term',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Account',
        required=True,
        domain=[('internal_type', '=', 'other')],
        help="The partner account used for this invoice."
    )
    document_number = fields.Char(
        string=u"Document Nº",
        required=True,
    )
    date = fields.Date(
        string=u'Financial date',
        default=fields.Date.context_today,
    )
    amount_total = fields.Monetary(
        string=u'Total',
        readonly=True,
        compute='_compute_totals',
    )
    amount_discount = fields.Monetary(
        string=u'Discount',
    )
    note = fields.Text(
        string="Note",
    )
    journal_id = fields.Many2one(
        required=False,
    )
    bank_id = fields.Many2one(
        'res.partner.bank',
        string=u'Bank Account',
    )

    @api.onchange('payment_term_id', 'document_number',
                  'date', 'amount')
    def onchange_fields(self):
        res = {}
        if not (self.payment_term_id and self.document_number and
                self.date and self.amount > 0.00):
            return res

        computations = \
            self.payment_term_id.compute(self.amount, self.date)

        payment_ids = []
        for idx, item in enumerate(computations[0]):
            payment = dict(
                document_item=self.document_number + '/' + str(idx + 1),
                date_maturity=item[0],
                amount=item[1],
            )
            payment_ids.append((0, False, payment))
        self.line_ids = payment_ids

    @api.multi
    def compute(self):
        financial_move = self.env['financial.move']
        financial_type = False
        for record in self:
            for move in record.line_ids:
                vals = financial_move._prepare_payment(
                    bank_id=self.bank_id.id,
                    company_id=self.company_id.id,
                    currency_id=self.currency_id.id,
                    financial_type=self.financial_type,
                    partner_id=self.partner_id.id,
                    document_number=move.document_item,
                    date=self.date,
                    payment_mode_id=self.payment_mode_id.id,
                    payment_term_id=self.payment_term_id.id,
                    analytic_account_id=self.analytic_account_id.id,
                    account_id=self.account_id.id,
                    date_maturity=move.date_maturity,
                    amount=move.amount,
                )
                financial = financial_move.create(vals)
                financial.action_confirm()
                financial_move |= financial
                financial_type = record.financial_type

        return financial_move.action_view_financial(financial_type)


class FinancialMoveLineCreate(models.TransientModel):

    _name = 'financial.move.line.create'

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Currency',
    )

    document_item = fields.Char(
        string=u"Document item",
    )

    date = fields.Date(
        string=u"Document date",
    )

    date_maturity = fields.Date(
        string=u"Due date",
    )

    amount = fields.Monetary(
        string=u"Document amount",
    )

    financial_move_id = fields.Many2one(
        comodel_name='financial.move.create',
        required=True
    )
