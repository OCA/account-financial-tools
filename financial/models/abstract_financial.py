# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from ..constants import (
    FINANCIAL_TYPE,
    FINANCIAL_STATE,
)


class AbstractFinancial(models.AbstractModel):
    _name = 'abstract.financial'
    # _description = '''Contains the logic shared between models which
    #     allows to register financial moves'''

    def _readonly_state(self):
        return {}

    def _required_fields(self):
        return False

    def _track_visibility_onchange(self):
        return False

    type = fields.Selection(
        string='Financial Type',
        selection=FINANCIAL_TYPE,
        required=True,
    )
    payment_method_id = fields.Many2one(
        comodel_name='account.payment.method',
        string='Payment Method Type',
        oldname="payment_method",
    )
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode',
        string="Payment Mode",
        ondelete='restrict',
        required=_required_fields,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    amount_document = fields.Float(
        string='Payment Amount',
        required=_required_fields,
        track_visibility=_track_visibility_onchange,
    )
    amount_discount = fields.Monetary(
        string=u'Discount',
        track_visibility=_track_visibility_onchange,
    )
    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        required=_required_fields,
        default=lambda self: self.env.user.company_id.currency_id,
        track_visibility=_track_visibility_onchange,
    )
    payment_date = fields.Date(
        string='Payment Date',
        default=fields.Date.context_today,
        required=_required_fields,
        copy=False,
    )
    document_date = fields.Date(
        string=u'Document date',
        track_visibility=_track_visibility_onchange,
    )
    date_maturity = fields.Date(
        string=u'Maturity date',
        track_visibility=_track_visibility_onchange,
    )
    communication = fields.Char(
        string='Memo',
    )
    bank_id = fields.Many2one(
        string=u'Bank Account',
        comodel_name='res.partner.bank',
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id.id,
        required=True,
    )
    note = fields.Text(
        string='Note',
        track_visibility=_track_visibility_onchange,
    )
    state = fields.Selection(
        selection=FINANCIAL_STATE,
        string=u'Status',
        index=True,
        readonly=True,
        default='draft',
        track_visibility='onchange',
        copy=False,
    )
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode',
        string="Payment Mode",
        ondelete='restrict',
        readonly=_required_fields,
        states=_readonly_state,
    )
    payment_term_id = fields.Many2one(
        string=u'Payment term',
        comodel_name='account.payment.term',
        track_visibility='onchange',
        required=False,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account'
    )
    account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Account',
        index=True,
        required=True,
        domain=[('type', '=', 'A')],
    )
    document_number = fields.Char(
        string=u"Document Nº",
        required=True,
        track_visibility=_track_visibility_onchange,
    )
    document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Document type',
        ondelete='restrict',
        index=True,
        required=True,
    )

    @api.multi
    @api.constrains('amount_document')
    def _check_amount(self):
        for record in self:
            if not record.amount_document > 0.0:
                raise ValidationError(_(
                    'The payment amount must be strictly positive.'))
