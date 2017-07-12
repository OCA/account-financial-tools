# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning as UserError
from odoo.tools import float_is_zero

from ..constants import (
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_DEBT_2PAY,
    FINANCIAL_PAYMENT_STATE,
    FINANCIAL_STATE,
    FINANCIAL_SEQUENCE,
    FINANCIAL_TYPE,
)


class FinancialMove(models.Model):
    _name = b'financial.move'
    _description = 'Financial Move'
    _inherit = ['mail.thread']
    _order = 'date_business_maturity desc, ' \
             'ref desc, ref_item desc, document_number, id desc'
    _rec_name = 'ref'

    @api.depends('date_business_maturity')
    def _compute_date_state(self):
        for record in self:
            hoje = fields.Date.context_today(record)
            vencimento = record.date_business_maturity
            if record.state == 'open' and hoje > vencimento:
                record.date_state = 'overdue'
            elif record.state == 'open' and hoje == vencimento:
                record.date_state = 'due_today'
            else:
                record.date_state = 'open'

    date_state = fields.Selection(
        string=u'Date State',
        selection=[
            ('open', 'Open'),
            ('overdue', 'Overdue'),
            ('due_today', 'Due today'),
        ],
        compute='_compute_date_state',
        store=True
    )
    #
    # Move identification
    #
    type = fields.Selection(
        string='Financial Type',
        selection=FINANCIAL_TYPE,
        required=True,
        index=True,
    )
    sign = fields.Integer(
        string='Sign',
        compute='_compute_sign',
        store=True,
    )
    state = fields.Selection(
        selection=FINANCIAL_STATE,
        string='Status',
        index=True,
        readonly=True,
        default='draft',
        track_visibility='onchange',
        copy=False,
    )
    #
    # TODO: Converter este campo em um similar ao semáforo de projetos
    #
    payment_state = fields.Selection(
        selection=FINANCIAL_PAYMENT_STATE,
        string='Financial Status',
        index=True,
        readonly=True,
        track_visibility='onchange',
        copy=False,
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
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Bank Account',
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

    #
    # Move dates; there are those five date fields, controlling, respectively:
    # date_document - when de document to which the move refers was created
    # date_maturity - up to when the debt must be paid
    # date_business_maturity - if date_maturity is a weekend, when banks don't
    #    regularly open, or is on a weekday, that happens to be a holiday,
    #    moves the *real* date_maturity to the next business day; when
    #    controlling customers' payments' regularity, if the customer pays
    #    his/her debt on the date_business_maturity, it must still be
    #    considered a regular paying customer
    # date_payment - when the debt was actually paid
    # date_credit_debit - when *the bank* credits/debits the actual money
    #    in/out of the bank account (in certain cases, there is a 1 or 2 day
    #    delay between the customer payment and the actual liquidity of the
    #    payment on the bank account
    #
    date_document = fields.Date(
        string='Document date',
        default=fields.Date.context_today,
    )
    date_maturity = fields.Date(
        string='Maturity date',
    )
    date_business_maturity = fields.Date(
        string='Business maturity date',
        store=True,
        compute='_compute_date_business_maturity'
    )
    date_payment = fields.Date(
        string='Payment date',
    )
    date_credit_debit = fields.Date(
        string='Credit/debit date',
    )
    date_cancel = fields.Date(
        string='Cancel date',
    )
    date_refund = fields.Date(
        string='Refund date',
    )

    #
    # Move amounts
    #
    amount_document = fields.Monetary(
        string='Document',
    )
    amount_interest = fields.Monetary(
        string='Interest',
    )
    amount_penalty = fields.Monetary(
        string='Penalty',
    )
    amount_other_credits = fields.Monetary(
        string='Other credits',
    )
    amount_discount = fields.Monetary(
        string='Discount',
    )
    amount_other_debits = fields.Monetary(
        string='Other debits',
    )
    amount_bank_fees = fields.Monetary(
        string='Bank fees',
    )
    amount_refund = fields.Monetary(
        string='Refund',
        copy=False,
    )
    amount_cancel = fields.Monetary(
        string='Cancelled',
        copy=False,
    )
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_totals',
        store=True,
    )
    amount_paid = fields.Monetary(
        string='Paid',
        compute='_compute_residual',
        store=True,
    )
    amount_residual = fields.Float(
        string='Residual',
        compute='_compute_residual',
        store=True,
    )

    #
    # Move interest and discount forecast
    #
    interest_rate = fields.Float(
        string='Interest rate',
        digits=(18, 10),
    )
    date_interest = fields.Date(
        string='Interest since',
    )
    amount_interest_forecast = fields.Monetary(
        string='Interest forecast',
    )
    penalty_rate = fields.Float(
        string='Penalty rate',
        digits=(18, 10),
    )
    date_penalty = fields.Date(
        string='Penalty since',
    )
    amount_penalty_forecast = fields.Monetary(
        string='Penalty forecast',
    )
    discount_rate = fields.Float(
        string='Penalty rate',
        digits=(18, 10),
    )
    date_discount = fields.Date(
        string='Discount up to',
    )
    amount_discount_forecast = fields.Monetary(
        string='Discount forecast',
    )
    amount_total_forecast = fields.Monetary(
        string='Total forecast',
    )

    #
    # Relations to other debts and payments
    #
    debt_id = fields.Many2one(
        comodel_name='financial.move',
        string='Debt',
        domain=[('type', 'in', (
            FINANCIAL_DEBT_2RECEIVE,
            FINANCIAL_DEBT_2PAY,
        ))]
    )
    payment_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='debt_id',
    )
    # financial_payment_id = fields.Many2one(
    #     comodel_name='financial.move',
    # )

    #
    # Notes
    #
    communication = fields.Char(
        string='Memo',
        track_visibility='_track_visibility_onchange',
    )
    note = fields.Text(
        string='Note',
        track_visibility='_track_visibility_onchange',
    )

    @api.depends('type')
    def _compute_sign(self):
        for move in self:
            if move.type in ['2receive', 'receipt_item', 'money_in']:
                move.sign = 1
            else:
                move.sign = -1

    @api.depends('amount_document',
                 'amount_penalty', 'amount_interest', 'amount_other_credits',
                 'amount_discount', 'amount_other_debits', 'amount_bank_fees',
                 'amount_refund', 'amount_cancel')
    def _compute_totals(self):
        for record in self:
            amount_total = record.amount_document
            amount_total += record.amount_interest
            amount_total += record.amount_penalty
            amount_total += record.amount_other_credits
            amount_total -= record.amount_discount
            amount_total -= record.amount_other_debits
            amount_total -= record.amount_bank_fees
            amount_total -= record.amount_refund
            amount_total -= record.amount_cancel
            record.amount_total = amount_total

    @api.multi
    @api.depends('state', 'currency_id', 'amount_total',
                 'payment_ids.amount_total')
    def _compute_residual(self):
        for record in self:
            amount_paid = 0.00
            if record.type in (FINANCIAL_DEBT_2RECEIVE, FINANCIAL_DEBT_2PAY):
                for payment in record.payment_ids:
                    amount_paid += payment.amount_document
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

    @api.depends('ref', 'ref_item')
    def _compute_display_name(self):
        for record in self:
            if record.ref_item:
                record.display_name = record.ref + '/' + record.ref_item
            else:
                record.display_name = record.ref or ''

    @api.depends('date_maturity')
    def _compute_date_business_maturity(self):
        # for move in self:
        #     if move.date_maturity:
        #         move.date_business_maturity = move.date_maturity
        # # TODO: refactory for global OCA use avoiding l10n_br_resource
        for record in self:
            if record.date_maturity:
                record.date_business_maturity = self.env[
                    'resource.calendar'].proximo_dia_util_bancario(
                    fields.Date.from_string(record.date_maturity))

    def _readonly_state(self):
        return {'draft': [('readonly', False)]}

    def _required_fields(self):
        return True

    def _track_visibility_onchange(self):
        return 'onchange'

    ref = fields.Char(
        required=True,
        copy=False,
        readonly=True,
        states='_readonly_state',
        index=True,
        default=lambda self: _('New')
    )
    ref_item = fields.Char(
        string='ref item',
        readonly=True,
        states='_readonly_state',
    )
    display_name = fields.Char(
        string='Financial Reference',
        compute='_compute_display_name',
    )
    reconciled = fields.Boolean(
        string='Paid/Reconciled',
        store=True,
        readonly=True,
        compute='_compute_residual',
    )
    doc_source_id = fields.Reference(
        selection=[],
        string='Source Document',
        readonly=True,
    )

    @api.multi
    @api.constrains('amount_document')
    def _check_amount(self):
        for record in self:
            if not (record.amount_document > 0.0 and
                    record.state not in 'cancel'):
                raise ValidationError(_(
                    'The payment amount must be strictly positive.'
                ))

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'open'),
            ('open', 'paid'),
            ('open', 'cancel'),
            ('paid', 'open'),
        ]
        return (old_state, new_state) in allowed

    @api.multi
    def action_number(self):
        for record in self:
            if record.ref == _('New'):
                sequencial_ids = self.search([
                    ('document_number', '=', record.document_number),
                ], order='date_business_maturity')
                if self.search_count([
                    ('document_number', '=', record.document_number),
                    ('ref', '=', _('New')),
                ]) == len(sequencial_ids.ids):
                    sequencial_ids.write({
                        'ref': self.env['ir.sequence'].next_by_code(
                            FINANCIAL_SEQUENCE[
                                record.type]) or 'New'
                    })
                    for i, x in enumerate(sequencial_ids):
                        x.ref_item = i + 1

    def do_before_create(self, values):
        return values

    @api.model
    def create(self, values):
        values = self.do_before_create(values)
        result = super(FinancialMove, self).create(values)
        return self.do_after_create(result, values)

    def do_after_create(self, result, values):
        return result

    def do_before_write(self, values):
        return values

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

    def do_after_write(self, result, values):
        return result

    def do_before_unlink(self):
        for financial in self:
            if financial.state not in ('draft', 'cancel'):
                if financial.doc_source_id:
                    # TODO: Improve this validation!
                    raise UserError(
                        _('You cannot delete an financial move which is \n'
                          'related to another document \n'
                          'try to cancel the related document'))
                raise UserError(
                    _('You cannot delete an financial move which is not \n'
                      'draft or cancelled'))

    @api.multi
    def unlink(self):
        self.do_before_unlink()
        result = super(FinancialMove, self).unlink()
        result = self.do_after_unlink(result)
        return result

    def do_after_unlink(self, result):
        return result

    @api.multi
    def change_state(self, new_state):
        for record in self:
            if record._avaliable_transition(record.state, new_state):
                record.state = new_state
            elif record.state == new_state:
                return True
            else:
                raise UserError(_('This state transition is not allowed'))

    @api.multi
    def action_confirm(self):
        for record in self:
            record.change_state('open')
        self.action_number()

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
                new_note = record.note + '\nCancel reason: ' + reason
            else:
                new_note = 'Cancel reason: ' + reason
            record.write({
                'amount_cancel': record.amount_document,
                'note': new_note
            })

    @staticmethod
    def _prepare_financial_move(
            date_maturity,
            amount,
            document_number,
            partner_id, type, date,
            bank_id, company_id, currency_id,
            analytic_account_id=False, account_type_id=False,
            payment_term_id=False,
            **kwargs):
        return dict(
            bank_id=bank_id,
            company_id=company_id,
            currency_id=currency_id,
            type=type,
            partner_id=partner_id,
            document_number=document_number,
            date=date,
            payment_term_id=payment_term_id,
            analytic_account_id=analytic_account_id,
            account_type_id=account_type_id,
            date_maturity=date_maturity,
            amount=amount,
            **kwargs
        )

    @api.multi
    def action_view_financial(self, type):
        if type == '2receive':
            action = self.env.ref(
                'financial.financial_receivable_act_window').read()[0]
        elif type == '2pay':
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

    def cron_interest(self):
        if self.env['resource.calendar'].data_eh_dia_util_bancario(
                datetime.today()):
            record = self.search([
                ('state', '=', 'open'),
                ('date_business_maturity', '<', datetime.today())])
            # record._compute_interest()
            record._compute_date_state()

    @api.depends('payment_mode_id', 'amount_document', 'date_business_maturity')
    def _compute_interest(self):
        for record in self:
            if self.env['resource.calendar']. \
                    data_eh_dia_util_bancario(datetime.today()) and record. \
                    state == 'open' and \
                    (datetime.today() > datetime.strptime
                        (record.date_business_maturity, '%Y-%m-%d')):
                day = (
                    datetime.today() - datetime.strptime(
                        record.date_maturity,
                        '%Y-%m-%d'))
                interest = record.amount_document * (record.payment_mode_id.
                                            interest_percent * day.days) / 100

                delay_fee = (record.payment_mode_id.
                             delay_fee_percent / 100) * record.amount_document
                record.amount_interest = interest + delay_fee

    def _create_from_dict(self, move_dict):
        '''How to use:

   def _prepare_lancamento_item(self, item):
        return {
            'document_number':
                '{0.serie}-{0.numero:0.0f}-{1.numero}/{2}'.format(
                    self, item, len(self.duplicata_ids)),
            'date_maturity': item.data_vencimento,
            'amount': item.valor
        }

    def _prepare_lancamento_financeiro(self):
        return {
            'date': self.data_emissao,
            'type': '2receive',
            'partner_id':
                self.participante_id and self.participante_id.partner_id.id,
            'doc_source_id': self._name + ',' + str(self.id),
            'bank_id': 1,
            'company_id': self.empresa_id and self.empresa_id.company_id.id,
            'currency_id': self.currency_id.id,
            'payment_term_id':
                self.payment_term_id and self.payment_term_id.id or False,
            # 'account_type_id':
            # 'analytic_account_id':
            # 'payment_mode_id:
            'lines': [self._prepara_lancamento_item(parcela)
                      for parcela in self.duplicata_ids],
        }

    def action_financial_create(self):

        p = self._prepare_lancamento_financeiro()
        financial_move_ids = self.env['financial.move']._create_from_dict(p)
        financial_move_ids.action_confirm()

        :param move_dict:
        :return: a record set of financial.move
        '''
        lines = move_dict.pop('lines')

        financial_move_ids = self.env['financial.move']

        for item in lines:
            date_maturity = item.pop('date_maturity')
            amount = item.pop('amount')
            document_number = item.pop('document_number')
            #
            # Override move_dict with item data!
            #
            kwargs = move_dict.copy()
            kwargs.update(item)

            values = self._prepare_financial_move(
                date_maturity=date_maturity,
                amount=amount,
                document_number=document_number,
                **kwargs
            )
            financial = self.create(values)
            financial_move_ids |= financial
        return financial_move_ids
