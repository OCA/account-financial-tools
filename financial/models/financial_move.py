# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

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


class FinancialMove(models.Model):
    _name = 'financial.move'
    _description = 'Financial Move'
    _inherit = ['mail.thread', 'account.abstract.payment']
    _order = "date_business_maturity desc, " \
             "ref desc, ref_item desc, document_number, id desc"
    _rec_name = 'ref'

    def _readonly_state(self):
        return {'draft': [('readonly', False)]}

    @api.multi
    @api.depends('ref', 'ref_item')
    def _compute_display_name(self):
        for record in self:
            if record.ref_item:
                record.display_name = record.ref + '/' + record.ref_item
            else:
                record.display_name = record.ref or ''

    @api.multi
    @api.depends('financial_type')
    def _compute_payment_type(self):
        for record in self:
            if record.financial_type in ('r', 'rr'):
                record.payment_type = 'inbound'
            elif record.financial_type in ('p', 'pp'):
                record.payment_type = 'outbound'

    @api.multi
    @api.depends('date_maturity')
    def _compute_date_business_maturity(self):
        # TODO: refactory for global OCA use
        for record in self:
            if record.date_maturity:
                record.date_business_maturity = self.env[
                    'resource.calendar'].proximo_dia_util_bancario(
                    fields.Date.from_string(record.date_maturity))

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'open'),
            ('open', 'paid'),
            ('open', 'cancel'),
        ]
        return (old_state, new_state) in allowed

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0 and self.state not in 'cancel':
            raise ValidationError(
                'The payment amount must be strictly positive.')

    @api.depends('amount', 'amount_interest', 'amount_discount',
                 'amount_refund', 'amount_cancel')
    def _compute_totals(self):
        for record in self:
            record.amount_total = (
                record.amount +
                record.amount_interest -
                record.amount_discount -
                record.amount_refund -
                record.amount_cancel
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
    financial_type = fields.Selection(
        selection=FINANCIAL_TYPE,
        required=True,
    )
    payment_type = fields.Selection(
        compute='_compute_payment_type',
    )
    payment_term_id = fields.Many2one(
        string=u'Payment term',
        comodel_name='account.payment.term',
        track_visibility='onchange',
    )
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account'
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Account',
        # required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        domain=[('deprecated', '=', False)],
        help="The partner account used for this invoice."
    )
    ref = fields.Char(
        string=u'Ref',
        required=True,
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
        default=lambda self: _('New')
    )
    ref_item = fields.Char(
        string=u"ref item",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    display_name = fields.Char(
        string=u'Financial Reference',
        compute='_compute_display_name',
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
    date_issue = fields.Date(
        string=u'Financial date',
        default=fields.Date.context_today,
    )
    date_maturity = fields.Date(
        string=u'Maturity date',
    )
    date_business_maturity = fields.Date(
        string=u'Business maturity',
        readonly=True,
        store=True,
        compute='_compute_date_business_maturity'
    )
    date_payment = fields.Date(
        string=u'Payment date',
        readonly=True,
        default=False,
    )
    date_credit_debit = fields.Date(
        string=u'Credit debit date',
        readonly=True,
    )
    amount_total = fields.Monetary(
        string=u'Total',
        readonly=True,
        compute='_compute_totals',
        store=True,
        index=True
    )
    amount_paid = fields.Monetary(
        string=u'Paid',
        readonly=True,
        # required=True
    )
    amount_discount = fields.Monetary(
        string=u'Discount',
        # required=True
    )
    amount_interest = fields.Monetary(
        string=u'Interest',
        readonly=True,
        # required=True
    )
    amount_refund = fields.Monetary(
        string=u'Refund',
        readonly=True,
        # required=True
    )
    amount_residual = fields.Monetary(
        string=u'Residual',
        readonly=True,
        # required=True
    )
    amount_cancel = fields.Monetary(
        string=u'Cancel',
        readonly=True,
        # required=True
    )
    note = fields.Text(
        string="Note",
        track_visibility='onchange',
    )

    def _before_create(self, values):
        if values.get('name', 'New') == 'New':
            if values.get('move_type') == 'r':
                values['ref'] = self.env['ir.sequence'].next_by_code(
                    'financial.move.receivable') or 'New'
                if not values.get('ref_item'):
                    values['ref_item'] = '1'
            elif values.get('move_type') == 'p':
                values['ref'] = self.env['ir.sequence'].next_by_code(
                    'financial.move.payable') or 'New'
                if not values.get('ref_item'):
                    values['ref_item'] = '1'
            else:
                values['ref'] = self.env['ir.sequence'].next_by_code(
                    'financial.move.receipt') or 'New'
                if not values.get('ref_item'):
                    values['ref_item'] = '1'

    @api.model
    def create(self, values):
        self._before_create(values)
        result = super(FinancialMove, self).create(values)
        return self._after_create(result)

    def _after_create(self, result):
        return result

    @api.multi
    def change_state(self, new_state):
        for record in self:
            if record._avaliable_transition(record.state, new_state):
                record.state = new_state
            else:
                raise UserError(_("This state transition is not allowed"))

    @api.multi
    def action_confirm(self):
        for record in self:
            record.change_state('open')

    @api.multi
    def action_budget(self):
        for record in self:
            record.change_state('budget')

    @api.multi
    def action_paid(self):
        for record in self:
            record.change_state('paid')

    @api.multi
    def action_cancel(self, reason):
        for record in self:
            record.change_state('cancel')
            if record.note:
                new_note = record.note + u'\nCancel reason: ' + reason
            else:
                new_note = u'Cancel reason: ' + reason
            record.write({
                'amount_cancel': record.amount,
                'amount': 0.00,
                'note': new_note
            })

    # payment_id = fields.Many2one(
    #     'financial.move',
    # )
    # related_payment_ids = fields.One2many(
    #     comodel_name='financial.move',
    #     inverse_name='payment_id',
    #     readonly=True,
    # )

    # # percent_interest = fields.Float() #  TODO:
    # # percent_discount = fields.Float() #  TODO:
    # storno = fields.Boolean(
    #     string=u'Storno',
    #     readonly=True
    # )
    # printed = fields.Boolean(
    #     string=u'Printed',
    #     readonly=True
    # )
    # sent = fields.Boolean(
    #     string=u'Sent',
    #     readonly=True
    # )
    # regociated = fields.Boolean()
    # regociated_id = fields.Many2one(
    #     comodel_name='financial.move',
    # )
    # related_regociated_ids = fields.One2many(
    #     comodel_name='financial.move',
    #     inverse_name='regociated_id',
    # )
    # move_id = fields.Many2one('account.move', string=u'Journal Entry',
    #                           readonly=True, index=True, ondelete='restrict',
    #                           copy=False,
    #                           help="Link to the automatically generated "
    #                                "Journal Items.")
    # account_move_line_id = fields.Many2one(
    #     comodel_name='account.move.line',
    # )
    # payment_receivable_ids = fields.One2many(
    #     comodel_name='account.move.line',
    #     compute='_compute_payment_receivable_ids',
    # )
    #
    # @api.multi
    # @api.depends('account_move_line_id')
    # def _compute_payment_receivable_ids(self):
    #     for record in self:
    #         ids = []
    #         aml = record.account_move_line_id
    #         ids.extend([r.debit_move_id.id for r in
    #                     aml.matched_debit_ids] if
    #                    aml.credit > 0 else [r.credit_move_id.id for r in
    #                                         aml.matched_credit_ids])
    #         record.payment_receivable_ids = ids
    #         record.payment_receivable_ids |= record.account_move_line_id
    #
    #
    # @api.multi
    # @api.depends('related_payment_ids', 'amount_document')
    # def _compute_balance(self):
    #     for record in self:
    #
    #         if record.move_type in ('p', 'r'):
    #             balance = record.amount_document
    #             for payment in record.related_payment_ids:
    #                 balance -= (payment.amount_document +
    #                             payment.amount_discount -
    #                             payment.amount_interest -
    #                             payment.amount_delay_fee)
    #             record.balance = balance
    #         if record.balance <= 0 and record.related_payment_ids \
    #                 and record.state == 'open':
    #             record.change_state('paid')

    # def executa_antes_create(self, values):
    #     #
    #     # função de sobreescrita
    #     #
    #     if values.get('name', 'New') == 'New':
    #         if values.get('move_type') == 'r':
    #             values['ref'] = self.env['ir.sequence'].next_by_code(
    #                 'financial.move.receivable') or 'New'
    #             if not values.get('ref_item'):
    #                 values['ref_item'] = '1'
    #         elif values.get('move_type') == 'p':
    #             values['ref'] = self.env['ir.sequence'].next_by_code(
    #                 'financial.move.payable') or 'New'
    #             if not values.get('ref_item'):
    #                 values['ref_item'] = '1'
    #         else:
    #             values['ref'] = self.env['ir.sequence'].next_by_code(
    #                 'financial.move.receipt') or 'New'
    #             if not values.get('ref_item'):
    #                 values['ref_item'] = '1'
    #     pass
    #
    # def executa_depois_create(self, res):
    #     #
    #     # função de sobreescrita
    #     #
    #     # TODO: integração contabil
    #     if res and res.account_id.internal_type in ('receivable', 'payable'):
    #         res.sync_aml_lancamento_from_financeiro()
    #
    #     pass



    # def _prepare_aml(self):
    #     # partner_id = self.account_id = self.partner_id.property_account_receivable_id \
    #     # if self.voucher_type == 'sale' else
    #     # self.partner_id.property_account_payable_id
    #     credit = 0
    #     debit = 0
    #     if(self.move_type == 'receivable'):
    #         debit = self.amount_document
    #     else:
    #         credit = self.amount_document
    #     return dict(  # FIXME: change to account parameters
    #         name=self.display_name,
    #         date_maturity=self.date_due,
    #         date=self.document_date,
    #         company_id=self.company_id and self.company_id.id,
    #         currency_id=self.currency_id and self.currency_id.id,
    #         debit=debit,
    #         credit=credit,
    #         partner_id=self.partner_id and self.partner_id.id or False,
    #         internal_type=self.move_type,
    #         move_id=self.move_id,
    #         financial_move_id=self.id,
    #         account_id=self.account_id,
    #     )
    #
    # @api.multi
    # def sync_aml_lancamento_from_financeiro(self):
    #     # Se existir um financial que já tenha uma aml, atualizar o mesmo
    #
    #     # self, date_maturity, partner_id, internal_type,
    #     # company_id, currency_id, debit = 0, credit = 0, ** kwargs):
    #
    #     aml_obj = self.env['account.move.line'].create(
    #         self._prepare_aml())
    #     aml_obj.action_invoice_open()
    #     return True
