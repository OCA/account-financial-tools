# Copyright 2014-2016 Akretion - Mourad EL HADJ MIMOUNE
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.account.tests.account_test_classes\
    import AccountingTestCase
import time


class TestPayment(AccountingTestCase):

    def setUp(self):
        super(TestPayment, self).setUp()
        self.register_payments_model = self.env['account.register.payments']
        self.payment_model = self.env['account.payment']
        self.journal_model = self.env['account.journal']
        self.account_account_model = self.env['account.account']
        self.invoice_model = self.env['account.invoice']
        self.invoice_line_model = self.env['account.invoice.line']
        self.acc_bank_stmt_model = self.env['account.bank.statement']
        self.acc_bank_stmt_line_model = self.env['account.bank.statement.line']
        self.res_partner_bank_model = self.env['res.partner.bank']
        self.check_deposit_model = self.env['account.check.deposit']

        self.partner_agrolait = self.env.ref("base.res_partner_2")
        self.currency_eur_id = self.env.ref("base.EUR").id
        self.main_company = self.env.ref('base.main_company')
        self.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (self.main_company.id, self.currency_eur_id),
        )
        self.product = self.env.ref("product.product_product_4")
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in")
        self.payment_method_manual_out = self.env.ref(
            "account.account_payment_method_manual_out")
        # check if those accounts exist otherwise create them
        self.account_receivable = self.account_account_model.search(
            [('code', '=', '411100')], limit=1)

        if not self.account_receivable:
            self.account_receivable = self.account_account_model.create(
                {"code": '411100',
                 "name": "Debtors - (test)",
                 "reconcile": True,
                 "user_type_id":
                 self.ref('account.data_account_type_receivable')
                 })

        self.account_revenue = self.account_account_model.search(
            [('code', '=', '707100')], limit=1)
        if not self.account_revenue:
            self.account_revenue = self.account_account_model.create(
                {"code": '707100',
                 "name": "Product Sales - (test)",
                 "user_type_id":
                 self.ref('account.data_account_type_revenue')
                 })

        self.received_check_account_id = self.account_account_model.search(
            [('code', '=', '511200')], limit=1)
        if self.received_check_account_id:
            if not self.received_check_account_id.reconcile:
                self.received_check_account_id.reconcile = True
        else:
            self.received_check_account_id = self.account_account_model.create(
                {"code": '511200',
                 "name": "Received check - (test)",
                 "reconcile": True,
                 "user_type_id":
                 self.ref('account.data_account_type_liquidity')
                 })
        self.main_company.check_deposit_account_id = \
            self.account_account_model.search(
                [('code', '=', '511201')], limit=1)
        if not self.main_company.check_deposit_account_id:
            self.main_company.check_deposit_account_id = \
                self.account_account_model.create(
                    {"code": '511201',
                     "name": "Check deposited in bank - (test)",
                     "reconcile": True,
                     "user_type_id":
                     self.ref('account.data_account_type_liquidity')
                     })
        self.bank_account_id = self.account_account_model.search(
            [('code', '=', '512001')], limit=1)
        if not self.bank_account_id:
            self.bank_account_id = self.account_account_model.create(
                {"code": '512001',
                 "name": "Bank - (test)",
                 "reconcile": True,
                 "user_type_id":
                 self.ref('account.data_account_type_liquidity')
                 })

        self.check_journal = self.journal_model.search(
            [('code', '=', 'CHK')], limit=1)
        if not self.check_journal:
            self.check_journal = self.journal_model.create(
                {'name': 'received check', 'type': 'bank', 'code': 'CHK'})
        self.check_journal.default_debit_account_id = \
            self.received_check_account_id
        self.check_journal.default_credit_account_id = \
            self.received_check_account_id
        self.bank_journal = self.journal_model.search(
            [('code', '=', 'BNK1')], limit=1)
        if not self.bank_journal:
            self.bank_journal = self.journal_model.create(
                {'name': 'Bank', 'type': 'bank', 'code': 'BNK1'})
        self.bank_journal.default_debit_account_id = self.bank_account_id
        self.bank_journal.default_credit_account_id = self.bank_account_id
        self.partner_bank_id = self.res_partner_bank_model.search(
            [('partner_id', '=', self.main_company.partner_id.id)], limit=1)
        if not self.partner_bank_id:
            self.partner_bank_id = self.res_partner_bank_model.create(
                {"acc_number": 'SI56 1910 0000 0123 438 584',
                 "partner_id": self.main_company.partner_id.id,
                 })
        self.bank_journal.bank_account_id = self.partner_bank_id.id

    def create_invoice(self, amount=100, type='out_invoice', currency_id=None):
        """ Returns an open invoice """
        invoice = self.invoice_model.create({
            'partner_id': self.partner_agrolait.id,
            'reference_type': 'none',
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

    def create_check_deposit(self, move_lines):
        """ Returns an validated check deposit """
        check_deposit = self.check_deposit_model.create({
            'journal_id': self.bank_journal.id,
            'bank_journal_id': self.bank_journal.id,
            'deposit_date': time.strftime('%Y-%m-%d'),
            'currency_id': self.currency_eur_id,
        })
        for move_line in move_lines:
            move_line.check_deposit_id = check_deposit
        check_deposit.validate_deposit()
        return check_deposit

    def test_full_payment_process(self):
        """ Create a payment for on invoice by check,
         post it and create check deposit"""
        inv_1 = self.create_invoice(
            amount=100, currency_id=self.currency_eur_id)
        inv_2 = self.create_invoice(
            amount=200, currency_id=self.currency_eur_id)

        ctx = {
            'active_model': 'account.invoice',
            'active_ids': [
                inv_1.id,
                inv_2.id]}
        register_payments = self.register_payments_model.with_context(
            ctx).create({
                        'payment_date': time.strftime('%Y-%m-%d'),
                        'journal_id': self.check_journal.id,
                        'payment_method_id': self.payment_method_manual_in.id,
                        })
        register_payments.create_payments()
        payment = self.payment_model.search([], order="id desc", limit=1)

        self.assertAlmostEquals(payment.amount, 300)
        self.assertEqual(payment.state, 'posted')
        self.assertEqual(inv_1.state, 'paid')
        self.assertEqual(inv_2.state, 'paid')

        check_aml = payment.move_line_ids.filtered(
            lambda r: r.account_id == self.received_check_account_id)

        check_deposit = self.create_check_deposit([check_aml])
        liquidity_aml = check_deposit.move_id.line_ids.filtered(
            lambda r: r.account_id != self.received_check_account_id)

        self.assertEqual(check_deposit.total_amount, 300)
        self.assertEqual(liquidity_aml.debit, 300)
        self.assertEqual(check_deposit.move_id.state, 'draft')
        self.assertEqual(check_deposit.state, 'done')
