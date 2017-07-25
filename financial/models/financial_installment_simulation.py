# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import fields, models


class FinancialInstallmentPreview(models.Model):
    _name = b'financial.installment.simulation'
    _description = 'Financial Installment Simulation'
    _order = 'installment_id, date_maturity'

    installment_id = fields.Many2one(
        comodel_name='financial.installment',
        string='Installment',
    )
    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        related='installment_id.currency_id',
    )
    number = fields.Char(
        string='Number',
    )
    date_maturity = fields.Date(
        string='Due date',
    )
    amount_document = fields.Float(
        string='Document amount',
        digits=(18, 2),
    )
    move_id = fields.One2many(
        comodel_name='financial.move',
        inverse_name='installment_simulation_id',
        string='Financial move',
    )

    def prepare_financial_move(self):
        self.ensure_one()

        move_data = {
            'type': self.installment_id.type,
            'company_id': self.installment_id.company_id.id,
            'currency_id': self.installment_id.currency_id.id,
            'partner_id': self.installment_id.partner_id.id,
            'document_type_id': self.installment_id.document_type_id.id,
            'account_id': self.installment_id.account_id.id,
            'date_document': self.installment_id.date_document,
            'note': self.installment_id.note,
            'document_number': self.number,
            'date_maturity': self.date_maturity,
            'amount_document': self.amount_document,
            'installment_simulation_id': self.id,
        }

        return move_data

    def create_financial_move(self):
        self.ensure_one()

        if self.move_id:
            return self.move_id

        move_data = self.prepare_financial_move()
        move = self.env['financial.move'].create(move_data)
        return move
