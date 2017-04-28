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
    _description = """Contains the logic shared between models which
        allows to register financial moves"""

    def _readonly_state(self):
        return {}

    def _required_fields(self):
        return False

    def _track_visibility_onchange(self):
        return False

    financial_type = fields.Selection(
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
    amount = fields.Monetary(
        string='Payment Amount',
        required=_required_fields,
    )
    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        required=_required_fields,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    payment_date = fields.Date(
        string='Payment Date',
        default=fields.Date.context_today,
        required=_required_fields,
        copy=False,
    )
    communication = fields.Char(
        string='Memo',
    )
    bank_id = fields.Many2one(
        string=u'Bank Account',
        comodel_name='res.partner.bank',
        required=True,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
    )
    note = fields.Text(
        string='Note'
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
        required=_required_fields,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account'
    )
    account_type_id = fields.Many2one(
        comodel_name='account.account.type',
        string=u'Category',
        # required=_required_fields,
        # readonly=True,
        # states=_readonly_state,
        help="The partner account used for this invoice."
    )
    document_number = fields.Char(
        string=u"Document Nº",
        required=_required_fields,
        readonly=True,
        states=_readonly_state,
        track_visibility=_track_visibility_onchange,
    )

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0:
            raise ValidationError(_(
                'The payment amount must be strictly positive.'))
