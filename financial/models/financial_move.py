# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
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

FINANCIAL_SEQUENCE = {
    'r': 'financial.move.receivable',
    'rr': 'financial.move.receipt',
    'p': 'financial.move.payable',
    'pp': 'financial.move.payment',
}


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

    @api.depends('amount',
                 'amount_interest',
                 'amount_discount',
                 'amount_refund',
                 'amount_cancel',
                 )
    def _compute_totals(self):
        for record in self:
            amount_total = (
                record.amount +
                record.amount_interest -
                record.amount_discount -
                record.amount_refund -
                record.amount_cancel
            )
            record.amount_total = amount_total

    @api.multi
    @api.depends('state', 'currency_id', 'amount_total',
                 'related_payment_ids.amount_total')
    def _compute_residual(self):
        for record in self:
            amount_paid = 0.00
            if record.financial_type in ('r', 'p'):
                for payment in record.related_payment_ids:
                    amount_paid += payment.amount_total
                amount_residual = record.amount_total - amount_paid
                digits_rounding_precision = record.currency_id.rounding

                record.amount_residual = amount_residual
                record.amount_paid = amount_paid
                if float_is_zero(
                        amount_residual,
                        precision_rounding=digits_rounding_precision):
                    record.reconciled = True
                else:
                    record.reconciled = False

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
        required=False,
    )
    payment_method_id = fields.Many2one(
        required=False,
    )
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode', string="Payment Mode",
        ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)]})
    payment_term_id = fields.Many2one(
        string=u'Payment term',
        comodel_name='account.payment.term',
        track_visibility='onchange',
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
        domain=[('internal_type', 'in', ('receivable', 'payable'))],
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
        compute='_compute_residual',
        store=True,
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
        compute='_compute_residual',
        store=True,
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
    related_payment_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='financial_payment_id',
        readonly=True,
    )
    financial_payment_id = fields.Many2one(
        comodel_name='financial.move',
    )
    reconciled = fields.Boolean(
        string='Paid/Reconciled',
        store=True,
        readonly=True,
        compute='_compute_residual',
    )

    def _before_create(self, values):
        # TODO: call this method in action_confirm to avoid sequence gaps
        if values.get('name', 'New') == 'New':
            values['ref'] = self.env['ir.sequence'].next_by_code(
                    FINANCIAL_SEQUENCE[values.get('financial_type')]
            ) or 'New'
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
    def _write(self, vals):
        pre_not_reconciled = self.filtered(
            lambda financial: not financial.reconciled)
        pre_reconciled = self - pre_not_reconciled
        res = super(FinancialMove, self)._write(vals)
        reconciled = self.filtered(lambda financial: financial.reconciled)
        not_reconciled = self - reconciled
        (reconciled & pre_reconciled).filtered(
            lambda financial: financial.state == 'open').action_paid()
        (not_reconciled & pre_not_reconciled).filtered(
            lambda invoice: invoice.state == 'paid').action_estorno()
        return res

    @api.multi
    def unlink(self):
        for financial in self:
            if financial.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You cannot delete an financial move which is not \n'
                      'draft or cancelled'))
                if financial.document_number:
                    # TODO: Improve this validation!
                    raise UserError(
                        _('You cannot delete an financial move which is \n'
                          'generated by another document \n'
                          'try to cancel you document first'))
        return super(FinancialMove, self).unlink()

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
    def action_estorno(self):
        for record in self:
            record.change_state('open')

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

    @staticmethod
    def _prepare_payment(journal_id, company_id, currency_id,
                         financial_type, partner_id, document_number,
                         date_issue, document_item, date_maturity, amount,
                         account_analytic_id=False, account_id=False,
                         payment_term_id=False, payment_mode_id=False,
                         args={}):

        return dict(
            args,
            journal_id=journal_id,
            company_id=company_id,
            currency_id=currency_id,
            financial_type=financial_type,
            partner_id=partner_id,
            document_number=document_number,
            date_issue=date_issue,
            payment_mode_id=payment_mode_id,
            payment_term_id=payment_term_id,
            account_analytic_id=account_analytic_id,
            account_id=account_id,
            document_item=document_item,
            date_maturity=date_maturity,
            amount=amount,
        )

    @api.multi
    def action_view_financial(self, financial_type):
        if financial_type == 'r':
            action = self.env.ref(
                'financial.financial_receivable_act_window').read()[0]
        else:
            action = self.env.ref(
                'financial.financial_payable_act_window').read()[0]
        if len(self) > 1:
            action['domain'] = [('id', 'in', self.ids)]
        elif len(self) == 1:
            action['views'] = [
                (self.env.ref('financial.financial_move_form_view').id, 'form')
            ]
            action['res_id'] = self.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

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
