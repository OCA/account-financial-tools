# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import (
    FINANCIAL_MOVE,
)


class FinancialMoveCreate(models.TransientModel):

    _name = 'financial.move.create'
    _inherit = ['abstract.financial']

    @api.depends('amount', 'amount_discount')
    def _compute_totals(self):
        for record in self:
            record.amount_total = record.amount - record.amount_discount

    line_ids = fields.One2many(
        comodel_name='financial.move.line.create',
        inverse_name='financial_move_id',
        # readonly=True,
    )
    payment_term_id = fields.Many2one(
        string='Payment Term',
        comodel_name='account.payment.term',
        required=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account',
    )
    document_number = fields.Char(
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
        financial_move = self.env['financial.move'].create_contract(self)
        financial_type = financial_move and financial_move[0].financial_type
        return financial_move.action_view_financial(financial_type)


class FinancialMoveLineCreate(models.TransientModel):

    _name = 'financial.move.line.create'

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Currency',
    )
    document_item = fields.Char()
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
