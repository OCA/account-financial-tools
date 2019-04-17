# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models

from ..constants import (
    FINANCIAL_INSTALLMENT_STATE,
    FINANCIAL_INSTALLMENT_STATE_DRAFT,
    FINANCIAL_INSTALLMENT_STATE_CONFIRMED,
    FINANCIAL_TYPE,
)


class FinancialInstallment(models.Model):
    _name = 'financial.installment'
    _description = 'Financial Installment'
    _rec_name = 'document_number'

    #
    # Move identification
    #
    state = fields.Selection(
        selection=FINANCIAL_INSTALLMENT_STATE,
        string='Status',
        index=True,
        readonly=True,
        default=FINANCIAL_INSTALLMENT_STATE_DRAFT,
        track_visibility='onchange',
        copy=False,
    )
    type = fields.Selection(
        string='Financial Type',
        selection=FINANCIAL_TYPE,
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        ondelete='restrict',
        default=lambda self: self.env.user.company_id.id,
        index=True,
    )
    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        default=lambda self: self.env.user.company_id.currency_id,
        track_visibility='_track_visibility_onchange',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        ondelete='restrict',
        index=True,
    )
    document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Document type',
        ondelete='restrict',
        index=True,
        required=True,
    )
    document_number = fields.Char(
        string='Document number',
        index=True,
        required=True,
    )
    account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Account',
        index=True,
        required=True,
        domain=[('type', '=', 'A')],
    )
    date_document = fields.Date(
        string='Document date',
        default=fields.Date.context_today,
        index=True,
    )
    amount_document = fields.Float(
        string='Document Amount',
        digits=(18, 2),
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
        string='Note',
    )
    payment_term_id = fields.Many2one(
        string='Payment Term',
        comodel_name='account.payment.term',
        required=True,
    )
    simulation_ids = fields.One2many(
        comodel_name='financial.installment.simulation',
        inverse_name='installment_id',
        string='Installments (simulation)',
    )
    move_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='installment_id',
        string='Financial Moves',
    )

    @api.onchange('payment_term_id', 'document_number',
                  'date_document', 'amount_document')
    def _onchange_payment_term_id(self):
        if not (self.payment_term_id and self.document_number and
                self.date_document and self.amount_document > 0):
            return

        installments = self.payment_term_id.compute(
            self.amount_document, self.date_document)[0]
        installments_number = len(installments)

        self.simulation_ids = False
        simulation_ids = []

        for idx, installment in enumerate(installments):
            date_maturity, amount_document = installment
            number = self.document_number + '-' + str(idx + 1).zfill(2) + \
                '/' + str(installments_number).zfill(2)

            simulation_data = {
                'number': number,
                'date_maturity': date_maturity,
                'amount_document': amount_document,
                'installment_id': self.id,
            }
            simulation_ids.append(simulation_data)
        self.simulation_ids = simulation_ids

        # Retornar dict com informação das simulaçoes
        # Como o onchange nao instancia o objeto, as informações sao passadas
        # no dict para realizar testes unitarios
        return simulation_ids

    @api.multi
    def confirm(self):
        for installment in self:
            if installment.state != FINANCIAL_INSTALLMENT_STATE_DRAFT:
                continue

            for simulation in installment.simulation_ids:
                move = simulation.create_financial_move()
                move.action_confirm()

            installment.state = FINANCIAL_INSTALLMENT_STATE_CONFIRMED
