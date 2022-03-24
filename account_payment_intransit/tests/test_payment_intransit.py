# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError, UserError
import time


class TestAccountPaymentIntransit(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.invoice_model = self.env['account.invoice']
        self.register_payments_model = self.env['account.register.payments']
        self.payment_model = self.env['account.payment']
        self.journal_model = self.env['account.journal']
        self.account_account_model = self.env['account.account']
        self.invoice_line_model = self.env['account.invoice.line']
        self.move_line_model = self.env['account.move.line']
        self.res_partner_bank_model = self.env['res.partner.bank']
        self.payment_intransit_model = self.env['account.payment.intransit']
        self.payment_intransit_line_model = \
            self.env['account.payment.intransit.line']

        self.partner_agrolait = self.env.ref('base.res_partner_2')
        self.currency_eur_id = self.env.ref('base.EUR').id
        self.currency_usd_id = self.env.ref('base.USD').id
        self.main_company = self.env.ref('base.main_company')
        self.product = self.env.ref('product.product_product_4')
        self.payment_method_manual_in = self.env.ref(
            'account.account_payment_method_manual_in')
        self.main_company.payment_intransit_post_move = True

        self.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (self.main_company.id, self.currency_eur_id),
        )
        self.account_receivable = self.account_account_model.search(
            [('code', '=', '411100')], limit=1)
        if not self.account_receivable:
            self.account_receivable = self.account_account_model.create(
                {'code': '411100',
                 'name': 'Debtors - (test)',
                 'reconcile': True,
                 'user_type_id': 1
                 })

        self.account_type_revenue = self.env.ref(
            'account.data_account_type_revenue').id
        self.account_type_receivable = self.env.ref(
            'account.data_account_type_receivable').id
        self.account_receivable = self.account_account_model.search([
            ('user_type_id', '=', self.account_type_receivable)], limit=1)
        self.account_revenue = self.account_account_model.search([
            ('user_type_id', '=', self.account_type_revenue)], limit=1)

        # Create journal Bank Intransit
        self.intransit_account_id = self.account_account_model.search(
            [('code', '=', '111')], limit=1)
        if not self.intransit_account_id:
            self.intransit_account_id = self.account_account_model.create(
                {'code': '111',
                 'name': 'Intransit',
                 'reconcile': True,
                 'user_type_id': self.account_type_receivable
                 })
        self.journal_account = self.journal_model.search([
            ('code', '=', 'BIT')], limit=1)
        if not self.journal_account:
            self.journal_account = self.journal_model.create({
                'name': 'Bank Intransit',
                'type': 'bank',
                'code': 'BIT'})
        self.journal_account.default_debit_account_id = \
            self.intransit_account_id
        self.journal_account.default_credit_account_id = \
            self.intransit_account_id

        # Create Bank Account
        self.bank_account_id = self.account_account_model.search(
            [('code', '=', '222')], limit=1)
        if not self.bank_account_id:
            self.bank_account_id = self.account_account_model.create(
                {'code': '222',
                 'name': 'SCB',
                 'user_type_id': 3
                 })
        self.partner_bank_id = self.res_partner_bank_model.search(
            [('partner_id', '=', self.main_company.partner_id.id)], limit=1)
        if not self.partner_bank_id:
            self.partner_bank_id = self.res_partner_bank_model.create(
                {'acc_number': 'SCB 222 222 222',
                 'partner_id': self.main_company.partner_id.id,
                 })

        self.bank_journal = self.journal_model.search([
            ('code', '=', 'BNK1')], limit=1)
        if not self.bank_journal:
            self.bank_journal = self.journal_model.create({
                'name': 'SCB',
                'type': 'bank',
                'code': 'BNK1'})
        self.bank_journal.default_debit_account_id = self.bank_account_id
        self.bank_journal.default_credit_account_id = self.bank_account_id
        self.bank_journal.update_posted = True

    def create_invoice(self, amount=100, type='out_invoice', currency_id=None):
        """ Returns an open invoice """
        invoice = self.invoice_model.create({
            'partner_id': self.partner_agrolait.id,
            'currency_id': currency_id,
            'name': type == 'out_invoice' and
            'invoice to client' or 'invoice to supplier',
            'account_id': self.account_receivable.id,
            'type': type,
            'date_invoice': time.strftime('%Y-%m-%d'),
        })
        self.invoice_line_model.create({
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': amount,
            'invoice_id': invoice.id,
            'name': 'something',
            'account_id': self.account_revenue.id,
        })
        invoice.action_invoice_open()
        return invoice

    def create_payment_intransit(
            self, move_lines, allocation=None, curr_id=None):
        """ Returns an validated payment intransit """
        payment_intransit = self.payment_intransit_model.create({
            'partner_id': self.partner_agrolait.id,
            'journal_id': self.journal_account.id,
            'bank_journal_id': self.bank_journal.id,
            'intransit_date': time.strftime('%Y-%m-%d'),
            'currency_id': curr_id or self.main_company.currency_id.id,
        })
        for move_line in move_lines:
            self.payment_intransit_line_model.create({
                'move_line_id': move_line.id,
                'payment_intransit_type': 'cash',
                'allocation': allocation or 10,
                'intransit_id': payment_intransit.id
            })
        return payment_intransit

    def create_payment(self, ctx):
        register_payments = self.register_payments_model.with_context(
            ctx).create({
                'payment_date': time.strftime('%Y-%m-%d'),
                'journal_id': self.journal_account.id,
                'payment_method_id': self.payment_method_manual_in.id})
        register_payments.create_payments()

    def test_1_check_allocation(self):
        inv_1 = self.create_invoice(
            amount=100, currency_id=self.currency_eur_id)
        inv_2 = self.create_invoice(
            amount=200, currency_id=self.currency_eur_id)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [inv_1.id, inv_2.id]}
        self.create_payment(ctx)
        check_aml = self.move_line_model.search([]).filtered(
            lambda l: l.reconciled is False and l.debit > 0 and
            l.account_id == self.intransit_account_id)
        check_aml = self.move_line_model.search([])
        allocation = check_aml[0].amount_residual + 100
        payment_intransit = \
            self.create_payment_intransit(check_aml, allocation)
        with self.assertRaises(ValidationError):
            payment_intransit._check_allocation()

    def test_2_create_payment_intransit(self):
        """ Create payment intransit from invoice. """
        inv_1 = self.create_invoice(
            amount=100, currency_id=self.currency_eur_id)
        inv_2 = self.create_invoice(
            amount=200, currency_id=self.currency_eur_id)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [inv_1.id, inv_2.id]}
        self.create_payment(ctx)
        check_aml = self.move_line_model.search([]).filtered(
            lambda l: l.reconciled is False and l.debit > 0 and
            l.account_id == self.intransit_account_id)
        payment_intransit = self.create_payment_intransit(check_aml)
        for line in payment_intransit.intransit_line_ids:
            line.move_line_id.name_search(line.move_line_id.name)
        payment_intransit.validate_payment_intransit()
        payment_intransit.move_id.action_post()
        payment_intransit.onchange_company_id()
        payment_intransit.onchange_journal_id()
        payment_intransit.action_intransit_cancel()
        payment_intransit.backtodraft()
        payment_intransit.unlink()

    def test_3_create_diff_currency(self):
        inv_1 = self.create_invoice(
            amount=100, currency_id=self.currency_usd_id)
        inv_2 = self.create_invoice(
            amount=200, currency_id=self.currency_usd_id)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [inv_1.id, inv_2.id]}
        self.create_payment(ctx)
        check_aml = self.move_line_model.search([]).filtered(
            lambda l: l.reconciled is False and l.debit > 0 and
            l.account_id == self.intransit_account_id and
            l.currency_id == self.env.ref('base.USD'))
        allocation = check_aml[0].amount_residual_currency
        payment_intransit = self.create_payment_intransit(
            check_aml, allocation, self.currency_usd_id)
        payment_intransit.validate_payment_intransit()

    def test_4_configuration_account(self):
        inv_1 = self.create_invoice(
            amount=100, currency_id=self.currency_eur_id)
        inv_2 = self.create_invoice(
            amount=200, currency_id=self.currency_eur_id)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [inv_1.id, inv_2.id]}
        self.create_payment(ctx)
        check_aml = self.move_line_model.search([]).filtered(
            lambda l: l.reconciled is False and l.debit > 0 and
            l.account_id == self.intransit_account_id)
        payment_intransit = self.create_payment_intransit(check_aml)
        self.main_company.payment_intransit_offsetting_account = False
        with self.assertRaises(UserError):
            payment_intransit.validate_payment_intransit()
        self.main_company.payment_intransit_offsetting_account = 'bank_account'
        self.bank_journal.default_debit_account_id = False
        with self.assertRaises(UserError):
            payment_intransit.validate_payment_intransit()
        self.main_company.payment_intransit_offsetting_account = \
            'transfer_account'
        with self.assertRaises(UserError):
            payment_intransit.validate_payment_intransit()
        self.main_company.payment_intransit_transfer_account_id = \
            self.account_receivable
        payment_intransit.validate_payment_intransit()
