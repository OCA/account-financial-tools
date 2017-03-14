# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

FINANCIAL_MOVE = [
    ('r', u'Account Receivable'),
    ('p', u'Account Payable'),
]

FINANCIAL_IN_OUT = [
    ('rr', u'Receipt'),
    ('pp', u'Payment'),
]

FINANCIAL_TYPE = FINANCIAL_MOVE + FINANCIAL_IN_OUT

FINANCIAL_STATE = [
    ('draft', u'Draft'),
    ('open', u'Open'),
    ('paid', u'Paid'),
    ('cancel', u'Cancel'),
]


class FinancialMoveModel(models.AbstractModel):

    _name = 'financial.move.model'

    def _readonly_state(self):
        return {'draft': [('readonly', False)]}

    @api.model
    def _default_currency(self):
        # FIXME: Ao implementar o journal pegar a moeda do mesmo
        # journal = self._default_journal()
        # return journal.currency_id or journal.company_id.currency_id
        return self.env['res.company']._company_default_get(
            'financial.move').currency_id

    state = fields.Selection(
        selection=FINANCIAL_STATE,
        string='Status',
        index=True,
        readonly=True,
        default='draft',
        track_visibility='onchange',
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Company',
        required=True,
        readonly=True,
        states=_readonly_state,
        track_visibility='onchange',
        default=lambda self: self.env['res.company']._company_default_get(
            'financial.move'),
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        readonly=True,
        states=_readonly_state,
        track_visibility='onchange',
        default=_default_currency,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        readonly=True,
        states=_readonly_state,
        track_visibility='onchange',
    )
    document_number = fields.Char(
        string=u"Document Nº",
        required=True,
        readonly=True,
        states=_readonly_state,
        track_visibility='onchange',
    )
    document_item = fields.Char(
        string=u"Document item",
    )
    document_date = fields.Date(
        string=u"Document date",
        required=True,
        readonly=True,
        states=_readonly_state,
        track_visibility='onchange',
    )
    amount_document = fields.Monetary(
        string=u"Document amount",
        required=True,
        readonly=True,
        states=_readonly_state,
        track_visibility='onchange',
    )
    due_date = fields.Date(
        string=u"Due date",
        readonly=True,
        states=_readonly_state,
        track_visibility='onchange',
    )
    move_type = fields.Selection(
        selection=FINANCIAL_TYPE,
        required=True,
    )
    business_due_date = fields.Date(
        string='Business due date',
        compute='_compute_business_due_date',
        store=True,
        index=True,
        track_visibility='onchange',
    )
    payment_method_id = fields.Many2one(
        'account.payment.method',
        string='Payment Method Type',
        # required=True,
        oldname="payment_method"
    )
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        track_visibility='onchange',
    )

    @api.multi
    @api.constrains('amount_document')
    def _check_amount_document(self):
        for record in self:
            if record.amount_document <= 0:
                raise UserError(_(
                    "The amount document must be higher then ZERO!"))

    @api.multi
    @api.constrains('due_date')
    def _check_due_date(self):
        for record in self:
            if not record.due_date and record.move_type in ('p', 'r'):
                raise UserError(_(
                    "The financial move must have a due date!"))

    @api.multi
    @api.depends('due_date')
    def _compute_business_due_date(self):
        for record in self:
            if record.due_date:
                record.business_due_date = self.env[
                    'resource.calendar'].proximo_dia_util_bancario(
                        fields.Date.from_string(record.due_date))

