# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning as UserError

from ..constants import (
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_DEBT_2PAY,
    FINANCIAL_STATE,
    FINANCIAL_TYPE,
    FINANCIAL_TYPE_CODE,
    FINANCIAL_DEBT_STATUS,
    FINANCIAL_DEBT_STATUS_DUE,
    FINANCIAL_DEBT_STATUS_DUE_TODAY,
    FINANCIAL_DEBT_STATUS_OVERDUE,
    FINANCIAL_DEBT_STATUS_PAID,
    FINANCIAL_DEBT_STATUS_PAID_PARTIALLY,
    FINANCIAL_DEBT_STATUS_CANCELLED,
    FINANCIAL_DEBT_STATUS_CANCELLED_PARTIALLY,
    FINANCIAL_DEBT_STATUS_CONSIDERS_OPEN,
    FINANCIAL_DEBT_STATUS_CONSIDERS_PAID,
    FINANCIAL_DEBT_STATUS_CONSIDERS_CANCELLED,
    FINANCIAL_DEBT_CONCISE_STATUS,
    FINANCIAL_DEBT_CONCISE_STATUS_OPEN,
    FINANCIAL_DEBT_CONCISE_STATUS_PAID,
    FINANCIAL_DEBT_CONCISE_STATUS_CANCELLED,
)


class FinancialMove(models.Model):
    _name = b'financial.move'
    _description = 'Financial Move'
    _inherit = ['mail.thread']
    _order = 'date_business_maturity desc, ' \
             'ref desc, ref_item desc, document_number, id desc'
    _rec_name = 'display_name'

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
        index=True,
    )
    date_maturity = fields.Date(
        string='Maturity date',
        index=True,
    )
    date_business_maturity = fields.Date(
        string='Business maturity date',
        store=True,
        compute='_compute_date_business_maturity',
        index=True,
    )
    date_payment = fields.Date(
        string='Payment date',
        copy=False,
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
    amount_document = fields.Float(
        string='Document Amount',
        digits=(18, 2),
    )
    amount_interest = fields.Monetary(
        string='Interest',
        digits=(18, 2),
    )
    amount_penalty = fields.Monetary(
        string='Penalty',
        digits=(18, 2),
    )
    amount_other_credits = fields.Monetary(
        string='Other credits',
        digits=(18, 2),
    )
    amount_discount = fields.Monetary(
        string='Discount',
        digits=(18, 2),
    )
    amount_other_debits = fields.Monetary(
        string='Other debits',
        digits=(18, 2),
    )
    amount_bank_fees = fields.Monetary(
        string='Bank fees',
        digits=(18, 2),
    )
    amount_refund = fields.Float(
        string='Refund amount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_cancel = fields.Float(
        string='Cancelled amount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )

    #
    # Amount fields to sum up all payments linked to a debt
    #
    amount_paid_document = fields.Float(
        string='Paid Document Amount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_interest = fields.Float(
        string='Paid Interest',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_penalty = fields.Float(
        string='Paid Penalty',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_other_credits = fields.Float(
        string='Paid Other credits',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_discount = fields.Float(
        string='Paid Discount',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_other_debits = fields.Float(
        string='Paid Other debits',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_bank_fees = fields.Float(
        string='Paid Bank fees',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_paid_total = fields.Float(
        string='Paid Total',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
    )
    amount_residual = fields.Float(
        string='Residual',
        compute='_compute_total_and_residual',
        store=True,
        digits=(18, 2),
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
        digits=(18, 2),
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
        digits=(18, 2),
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
        digits=(18, 2),
    )
    amount_total_forecast = fields.Monetary(
        string='Total forecast',
        digits=(18, 2),
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
        ))],
        index=True,
    )
    payment_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='debt_id',
    )
    debt_ids = fields.One2many(
        comodel_name='financial.move',
        compute='_compute_debt_ids',
    )

    #
    # Debt status
    #
    debt_status = fields.Selection(
        string='Debt Status',
        selection=FINANCIAL_DEBT_STATUS,
        compute='_compute_debt_status',
        store=True,
        index=True,
    )
    debt_concise_status = fields.Selection(
        string='Debt Concise Status',
        selection=FINANCIAL_DEBT_CONCISE_STATUS,
        compute='_compute_debt_status',
        store=True,
        index=True,
    )
    reconciled = fields.Boolean(
        string='Paid/Reconciled',
        compute='_compute_debt_status',
        store=True,
        index=True,
    )

    #
    # Bank account where the money movement has taken place
    #
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Bank Account',
        ondelete='restrict',
        index=True,
    )

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

    #
    # Installments control
    #
    installment_simulation_id = fields.Many2one(
        comodel_name='financial.installment.simulation',
        string='Installment simulation',
        index=True,
        ondelete='restrict',
    )
    installment_id = fields.Many2one(
        comodel_name='financial.installment',
        string='Installment',
        related='installment_simulation_id.installment_id',
        readonly=True,
        store=True,
        index=True,
        ondelete='restrict',
    )

    #
    # Original currency and amount
    #
    original_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Original currecy',
    )
    original_currency_amount = fields.Float(
        string='Document amount in original currency',
        digits=(18, 2),
    )

    #
    #
    # Payment term and Payment mode
    #
    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode',
        string="Payment Mode",
    )
    # Este campo esta sendo inserido somente para fins gerenciais e não será
    # exibido na visão por enquanto.
    # TODO: Implementar um relatório que proporcione informações sobre o
    # ganho associado a diferentes condições de pagamentos.
    #
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string="Payment term",
    )

    @api.depends('type')
    def _compute_sign(self):
        for move in self:
            if move.type in ['2receive', 'receipt_item', 'money_in']:
                move.sign = 1
            else:
                move.sign = -1

    @api.depends('amount_document',
                 'amount_interest', 'amount_penalty', 'amount_other_credits',
                 'amount_discount', 'amount_other_debits', 'amount_bank_fees',
                 'payment_ids.amount_document',
                 'payment_ids.amount_interest', 'payment_ids.amount_penalty',
                 'payment_ids.amount_other_credits',
                 'payment_ids.amount_discount',
                 'payment_ids.amount_other_debits',
                 'payment_ids.amount_bank_fees',
                 )
    def _compute_total_and_residual(self):
        for move in self:
            amount_total = move.amount_document
            amount_total += move.amount_interest
            amount_total += move.amount_penalty
            amount_total += move.amount_other_credits
            amount_total -= move.amount_discount
            amount_total -= move.amount_other_debits
            amount_total -= move.amount_bank_fees

            amount_paid_document = 0
            amount_paid_interest = 0
            amount_paid_penalty = 0
            amount_paid_other_credits = 0
            amount_paid_discount = 0
            amount_paid_other_debits = 0
            amount_paid_bank_fees = 0
            amount_paid_total = 0

            amount_residual = 0
            amount_cancel = 0
            amount_refund = 0

            if move.type in (FINANCIAL_DEBT_2RECEIVE, FINANCIAL_DEBT_2PAY):
                for payment in move.payment_ids:
                    amount_paid_document += payment.amount_document
                    amount_paid_interest += payment.amount_interest
                    amount_paid_penalty += payment.amount_penalty
                    amount_paid_other_credits += payment.amount_other_credits
                    amount_paid_discount += payment.amount_discount
                    amount_paid_other_debits += payment.amount_other_debits
                    amount_paid_bank_fees += payment.amount_bank_fees
                    amount_paid_total += payment.amount_total

                amount_residual = amount_total - amount_paid_document

                if move.date_cancel:
                    amount_cancel = amount_residual

                if amount_residual < 0:
                    amount_refund = amount_residual * -1
                    amount_residual = 0

            move.amount_total = amount_total
            move.amount_residual = amount_residual
            move.amount_cancel = amount_cancel
            move.amount_refund = amount_refund
            move.amount_paid_document = amount_paid_document
            move.amount_paid_interest = amount_paid_interest
            move.amount_paid_penalty = amount_paid_penalty
            move.amount_paid_other_credits = amount_paid_other_credits
            move.amount_paid_discount = amount_paid_discount
            move.amount_paid_other_debits = amount_paid_other_debits
            move.amount_paid_bank_fees = amount_paid_bank_fees
            move.amount_paid_total = amount_paid_total

    @api.depends('ref', 'ref_item')
    def _compute_display_name(self):
        for record in self:
            financial_type = FINANCIAL_TYPE_CODE.get(record.type) or ''
            doc_type = '/' + record.document_type_id.name \
                if record.document_type_id.name else ''
            doc_number = '/' + record.document_number \
                         if record.document_number else ''
            partner = '-' + record.partner_id.name \
                if record.partner_id.name else ''

            record.display_name = (financial_type + doc_type + doc_number) \
                if not self._context.get('with_partner_name') \
                else (financial_type + doc_type + doc_number + partner)

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

    @api.depends('date_business_maturity', 'amount_total', 'amount_document',
                 'amount_residual', 'amount_paid_document', 'date_cancel')
    def _compute_debt_status(self):
        for move in self:
            if move.type not in (FINANCIAL_DEBT_2RECEIVE, FINANCIAL_DEBT_2PAY):
                continue

            if move.date_cancel:
                if move.amount_paid_document > 0:
                    move.debt_status = \
                        FINANCIAL_DEBT_STATUS_CANCELLED_PARTIALLY
                else:
                    move.debt_status = FINANCIAL_DEBT_STATUS_CANCELLED

            elif move.amount_paid_document > 0:
                if move.amount_residual > 0:
                    move.debt_status = FINANCIAL_DEBT_STATUS_PAID_PARTIALLY
                else:
                    move.debt_status = FINANCIAL_DEBT_STATUS_PAID

            else:
                today = fields.Date.context_today(move)
                due_date = move.date_business_maturity

                if due_date > today:
                    move.debt_status = FINANCIAL_DEBT_STATUS_DUE

                elif due_date == today:
                    move.debt_status = FINANCIAL_DEBT_STATUS_DUE_TODAY

                else:
                    move.debt_status = FINANCIAL_DEBT_STATUS_OVERDUE

            if move.debt_status in FINANCIAL_DEBT_STATUS_CONSIDERS_OPEN:
                move.debt_concise_status = FINANCIAL_DEBT_CONCISE_STATUS_OPEN
            elif move.debt_status in FINANCIAL_DEBT_STATUS_CONSIDERS_PAID:
                move.debt_concise_status = FINANCIAL_DEBT_CONCISE_STATUS_PAID
            elif move.debt_status in FINANCIAL_DEBT_STATUS_CONSIDERS_CANCELLED:
                move.debt_concise_status = \
                    FINANCIAL_DEBT_CONCISE_STATUS_CANCELLED

            if move.debt_status == FINANCIAL_DEBT_STATUS_PAID:
                move.reconciled = True
            else:
                move.reconciled = False

    @api.depends('debt_id')
    def _compute_debt_ids(self):
        for payment in self:
            if payment.debt_id:
                payment.debt_ids = [payment.debt_id.id]
            else:
                payment.debt_ids = False

    def _readonly_state(self):
        return {'draft': [('readonly', False)]}

    def _required_fields(self):
        return True

    def _track_visibility_onchange(self):
        return 'onchange'

    @api.depends('company_id.today_date')
    def _compute_arrears_days(self):
        def date_value(date_str):
            return fields.Date.from_string(date_str)
        for record in self:
            date_diference = False
            if record.debt_status == 'paid':
                date_diference = \
                    date_value(record.date_payment) - date_value(
                        record.date_business_maturity)
            elif record.debt_status == 'overdue':
                date_diference = \
                    date_value(record.company_id.today_date) - date_value(
                        record.date_business_maturity)
            arrears = date_diference and date_diference.days or 0
            record.arrears_days = arrears

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
        store=True,
    )
    doc_source_id = fields.Reference(
        selection=[],
        string='Source Document',
        readonly=True,
    )
    motivo_cancelamento_id = fields.Many2one(
        comodel_name="financial.move.motivo.cancelamento",
        string="Motivo do Cancelamento",
    )
    arrears_days = fields.Integer(
        string='Arrears Days',
        compute='_compute_arrears_days',
        store=True
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
            ('open', 'cancelled'),
            ('paid', 'open'),
        ]
        return (old_state, new_state) in allowed

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

    @api.multi
    def action_budget(self):
        for record in self:
            record.change_state('budget')

    @api.multi
    def action_paid(self):
        for record in self:
            record.change_state('paid')
            if record.state == 'paid':
                date_payment = \
                    max([x.date_payment for x in record.payment_ids])
                record.date_payment = date_payment

    @api.multi
    def action_estorno(self):
        for record in self:
            record.change_state('open')

    @api.multi
    def action_cancel(self, motivo_id, obs):
        for record in self:
            record.change_state('cancelled')
            if record.note:
                new_note = record.note + '\n' + obs
            else:
                new_note = obs
            record.write({
                'motivo_cancelamento_id': motivo_id,
                'amount_cancel': record.amount_document,
                'note': new_note,
                'amount_residual': 0,
            })
            record.with_context(no_email=True).message_post(body=new_note)

    @staticmethod
    def _prepare_financial_move(
            date_maturity,
            amount_document,
            document_number,
            partner_id, type, date_document,
            bank_id, company_id, currency_id,
            analytic_account_id=False, account_id=False,
            payment_term_id=False,
            **kwargs):
        return dict(
            bank_id=bank_id,
            company_id=company_id,
            currency_id=currency_id,
            type=type,
            partner_id=partner_id,
            document_number=document_number,
            date_document=date_document,
            payment_term_id=payment_term_id,
            analytic_account_id=analytic_account_id,
            account_id=account_id,
            date_maturity=date_maturity,
            amount_document=amount_document,
            **kwargs
        )

    @api.multi
    def action_view_financial(self, type):
        if type == '2receive':
            action = self.env.ref(
                'financial.financial_move_debt_2receive_form_action').read()[0]
        elif type == '2pay':
            action = self.env.ref(
                'financial.financial_move_debt_2pay_form_action').read()[0]
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
            record._compute_debt_status()

    @api.depends('payment_mode_id', 'amount_document',
                 'date_business_maturity')
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
                interest = record.amount_document * \
                    (record.payment_mode_id.interest_percent * day.days) / 100

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
            amount_document = item.pop('amount_document')
            document_number = item.pop('document_number')
            #
            # Override move_dict with item data!
            #
            kwargs = move_dict.copy()
            kwargs.update(item)

            values = self._prepare_financial_move(
                date_maturity=date_maturity,
                amount_document=amount_document,
                document_number=document_number,
                **kwargs
            )
            financial = self.create(values)
            financial_move_ids |= financial
        return financial_move_ids


class FinancialMoveMotivoCancelamento(models.Model):
    _name = b'financial.move.motivo.cancelamento'
    _rec_name = 'motivo_cancelamento'

    motivo_cancelamento = fields.Char(
        string="Motivo do Cancelamento",
        required=True,
    )
