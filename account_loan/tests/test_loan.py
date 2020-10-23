# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)
try:
    import numpy
except (ImportError, IOError) as err:
    _logger.error(err)


class TestLoan(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.browse_ref('base.main_company')
        self.company_02 = self.env['res.company'].create({
            'name': 'Auxiliar company'
        })
        self.journal = self.env['account.journal'].create({
            'company_id': self.company.id,
            'type': 'purchase',
            'name': 'Debts',
            'code': 'DBT',
        })
        self.loan_account = self.create_account(
            'DEP',
            'depreciation',
            self.browse_ref('account.data_account_type_current_liabilities').id
        )
        self.payable_account = self.create_account(
            'PAY',
            'payable',
            self.browse_ref('account.data_account_type_payable').id
        )
        self.asset_account = self.create_account(
            'ASSET',
            'asset',
            self.browse_ref('account.data_account_type_payable').id
        )
        self.interests_account = self.create_account(
            'FEE',
            'Fees',
            self.browse_ref('account.data_account_type_expenses').id)
        self.lt_loan_account = self.create_account(
            'LTD',
            'Long term depreciation',
            self.browse_ref(
                'account.data_account_type_non_current_liabilities').id)
        self.partner = self.env['res.partner'].create({
            'name': 'Bank'
        })
        self.product = self.env['product.product'].create({
            'name': 'Payment',
            'type': 'service'
        })
        self.interests_product = self.env['product.product'].create({
            'name': 'Bank fee',
            'type': 'service'
        })

    def test_onchange(self):
        loan = self.env['account.loan'].new({
            'name': 'LOAN',
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'loan_type': 'fixed-annuity',
            'loan_amount': 100,
            'rate': 1,
            'periods': 2,
            'short_term_loan_account_id': self.loan_account.id,
            'interest_expenses_account_id': self.interests_account.id,
            'product_id': self.product.id,
            'interests_product_id': self.interests_product.id,
            'partner_id': self.partner.id,
        })
        journal = loan.journal_id.id
        loan.is_leasing = True
        loan._onchange_is_leasing()
        self.assertNotEqual(journal, loan.journal_id.id)
        loan.company_id = self.company_02
        loan._onchange_company()
        self.assertFalse(loan.interest_expenses_account_id)

    def test_round_on_end(self):
        loan = self.create_loan('fixed-annuity', 500000, 1, 60)
        loan.round_on_end = True
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        for line in loan.line_ids:
            self.assertAlmostEqual(
                line_1.payment_amount, line.payment_amount, 2)
        loan.loan_type = 'fixed-principal'
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line_end = loan.line_ids.filtered(lambda r: r.sequence == 60)
        self.assertNotAlmostEqual(
            line_1.payment_amount, line_end.payment_amount, 2)
        loan.loan_type = 'interest'
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line_end = loan.line_ids.filtered(lambda r: r.sequence == 60)
        self.assertEqual(line_1.principal_amount, 0)
        self.assertEqual(line_end.principal_amount, 500000)

    def test_pay_amount_validation(self):
        amount = 10000
        periods = 24
        loan = self.create_loan('fixed-annuity', amount, 1, periods)
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            - numpy.pmt(1 / 100 / 12, 24, 10000), line.payment_amount, 2)
        self.assertEqual(line.long_term_principal_amount, 0)
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        self.assertFalse(line.invoice_ids)
        wzd = self.env['account.loan.generate.wizard'].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action['domain'][0][2])
        line.move_ids.post()
        with self.assertRaises(UserError):
            self.env['account.loan.pay.amount'].create({
                'loan_id': loan.id,
                'amount': (amount - amount / periods) / 2,
                'fees': 100,
                'date': datetime.strptime(
                    line.date, DF
                ).date() + relativedelta(months=-1)
            }).run()
        with self.assertRaises(UserError):
            self.env['account.loan.pay.amount'].create({
                'loan_id': loan.id,
                'amount': amount,
                'fees': 100,
                'date': datetime.strptime(
                    line.date, DF
                ).date()
            }).run()
        with self.assertRaises(UserError):
            self.env['account.loan.pay.amount'].create({
                'loan_id': loan.id,
                'amount': 0,
                'fees': 100,
                'date': datetime.strptime(
                    line.date, DF
                ).date()
            }).run()
        with self.assertRaises(UserError):
            self.env['account.loan.pay.amount'].create({
                'loan_id': loan.id,
                'amount': -100,
                'fees': 100,
                'date': datetime.strptime(
                    line.date, DF
                ).date()
            }).run()

    def test_fixed_annuity_begin_loan(self):
        amount = 10000
        periods = 24
        loan = self.create_loan('fixed-annuity-begin', amount, 1, periods)
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            - numpy.pmt(1 / 100 / 12, 24, 10000, when='begin'),
            line.payment_amount, 2)
        self.assertEqual(line.long_term_principal_amount, 0)
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        self.assertFalse(line.invoice_ids)
        wzd = self.env['account.loan.generate.wizard'].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action['domain'][0][2])
        line.move_ids.post()
        loan.rate = 2
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            - numpy.pmt(1 / 100 / 12, periods, amount, when='begin'),
            line.payment_amount, 2)
        line = loan.line_ids.filtered(lambda r: r.sequence == 2)
        self.assertAlmostEqual(
            - numpy.pmt(2 / 100 / 12, periods - 1,
                        line.pending_principal_amount, when='begin'),
            line.payment_amount, 2
        )
        line = loan.line_ids.filtered(lambda r: r.sequence == 3)
        with self.assertRaises(UserError):
            line.view_process_values()

    def test_fixed_annuity_loan(self):
        amount = 10000
        periods = 24
        loan = self.create_loan('fixed-annuity', amount, 1, periods)
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            - numpy.pmt(1 / 100 / 12, 24, 10000), line.payment_amount, 2)
        self.assertEqual(line.long_term_principal_amount, 0)
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        self.assertFalse(line.invoice_ids)
        wzd = self.env['account.loan.generate.wizard'].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action['domain'][0][2])
        line.move_ids.post()
        loan.rate = 2
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            - numpy.pmt(1 / 100 / 12, periods, amount), line.payment_amount, 2)
        line = loan.line_ids.filtered(lambda r: r.sequence == 2)
        self.assertAlmostEqual(
            - numpy.pmt(2 / 100 / 12, periods - 1,
                        line.pending_principal_amount),
            line.payment_amount, 2
        )
        line = loan.line_ids.filtered(lambda r: r.sequence == 3)
        with self.assertRaises(UserError):
            line.view_process_values()

    def test_fixed_principal_loan(self):
        amount = 24000
        periods = 24
        loan = self.create_loan('fixed-principal', amount, 1, periods)
        self.partner.property_account_payable_id = self.payable_account
        self.assertEqual(loan.journal_type, 'general')
        loan.is_leasing = True
        loan.post_invoice = False
        self.assertEqual(loan.journal_type, 'purchase')
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.rate_type = 'real'
        loan.compute_lines()
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertEqual(amount / periods, line.principal_amount)
        self.assertEqual(amount / periods, line.long_term_principal_amount)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.has_invoices)
        self.assertFalse(line.has_moves)
        action = self.env['account.loan.generate.wizard'].create({
            'date': fields.date.today(),
            'loan_type': 'leasing',
        }).run()
        self.assertTrue(line.has_invoices)
        self.assertFalse(line.has_moves)
        self.assertIn(line.invoice_ids.id, action['domain'][0][2])
        with self.assertRaises(UserError):
            self.env['account.loan.pay.amount'].create({
                'loan_id': loan.id,
                'amount': (amount - amount / periods) / 2,
                'fees': 100,
                'date': loan.line_ids.filtered(
                    lambda r: r.sequence == 2).date
            }).run()
        with self.assertRaises(UserError):
            self.env['account.loan.pay.amount'].create({
                'loan_id': loan.id,
                'amount': (amount - amount / periods) / 2,
                'fees': 100,
                'date': datetime.strptime(
                    loan.line_ids.filtered(lambda r: r.sequence == 1).date, DF
                ).date() + relativedelta(months=-1)
            }).run()
        line.invoice_ids.action_invoice_open()
        self.assertTrue(line.has_moves)
        self.assertIn(
            line.move_ids.id,
            self.env['account.move'].search(
                loan.view_account_moves()['domain']).ids
        )
        self.assertEqual(
            line.invoice_ids.id,
            self.env['account.invoice'].search(
                loan.view_account_invoices()['domain']).id
        )
        with self.assertRaises(UserError):
            self.env['account.loan.pay.amount'].create({
                'loan_id': loan.id,
                'amount': (amount - amount / periods) / 2,
                'fees': 100,
                'date': loan.line_ids.filtered(
                    lambda r: r.sequence == periods).date
            }).run()
        self.env['account.loan.pay.amount'].create({
            'loan_id': loan.id,
            'amount': (amount - amount / periods) / 2,
            'date': line.date,
            'fees': 100,
        }).run()
        line = loan.line_ids.filtered(lambda r: r.sequence == 2)
        self.assertEqual(loan.periods, periods + 1)
        self.assertAlmostEqual(
            line.principal_amount, (amount - amount / periods) / 2, 2)
        line = loan.line_ids.filtered(lambda r: r.sequence == 3)
        self.assertEqual(amount / periods / 2, line.principal_amount)
        line = loan.line_ids.filtered(lambda r: r.sequence == 4)
        with self.assertRaises(UserError):
            line.view_process_values()

    def test_fixed_principal_loan_auto_post(self):
        amount = 24000
        periods = 24
        loan = self.create_loan('fixed-principal', amount, 1, periods)
        self.partner.property_account_payable_id = self.payable_account
        self.assertEqual(loan.journal_type, 'general')
        loan.is_leasing = True
        self.assertEqual(loan.journal_type, 'purchase')
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.rate_type = 'real'
        loan.compute_lines()
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertEqual(amount / periods, line.principal_amount)
        self.assertEqual(amount / periods, line.long_term_principal_amount)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.has_invoices)
        self.assertFalse(line.has_moves)
        self.env['account.loan.generate.wizard'].create({
            'date': fields.date.today(),
            'loan_type': 'leasing',
        }).run()
        self.assertTrue(line.has_invoices)
        self.assertTrue(line.has_moves)

    def test_interests_on_end_loan(self):
        amount = 10000
        periods = 10
        loan = self.create_loan('interest', amount, 1, periods)
        loan.payment_on_first_period = False
        loan.start_date = fields.Date.today()
        loan.rate_type = 'ear'
        loan.compute_lines()
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        self.assertEqual(0, loan.line_ids[0].principal_amount)
        self.assertEqual(amount, loan.line_ids.filtered(
            lambda r: r.sequence == periods
        ).principal_amount)
        self.post(loan)
        self.assertEqual(loan.payment_amount, 0)
        self.assertEqual(loan.interests_amount, 0)
        self.assertEqual(loan.pending_principal_amount, amount)
        self.assertFalse(loan.line_ids.filtered(
            lambda r: (
                datetime.strptime(r.date, DF).date() <=
                datetime.strptime(loan.start_date, DF).date())))
        for line in loan.line_ids:
            self.assertEqual(loan.state, 'posted')
            line.view_process_values()
            line.move_ids.post()
        self.assertEqual(loan.state, 'closed')

        self.assertEqual(loan.payment_amount - loan.interests_amount, amount)
        self.assertEqual(loan.pending_principal_amount, 0)

    def test_cancel_loan(self):
        amount = 10000
        periods = 10
        loan = self.create_loan('fixed-annuity', amount, 1, periods)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line.view_process_values()
        line.move_ids.post()
        pay = self.env['account.loan.pay.amount'].create({
            'loan_id': loan.id,
            'amount': 0,
            'fees': 100,
            'date': line.date
        })
        pay.cancel_loan = True
        pay._onchange_cancel_loan()
        self.assertEqual(pay.amount, line.final_pending_principal_amount)
        pay.run()
        self.assertEqual(loan.state, 'cancelled')

    def post(self, loan):
        self.assertFalse(loan.move_ids)
        post = self.env['account.loan.post'].with_context(
            default_loan_id=loan.id
        ).create({})
        post.run()
        self.assertTrue(loan.move_ids)
        with self.assertRaises(UserError):
            post.run()

    def create_account(self, code, name, type_id):
        return self.env['account.account'].create({
            'company_id': self.company.id,
            'name': name,
            'code': code,
            'user_type_id': type_id,
            'reconcile': True,
        })

    def create_loan(self, type, amount, rate, periods):
        loan = self.env['account.loan'].create({
            'journal_id': self.journal.id,
            'rate_type': 'napr',
            'loan_type': type,
            'loan_amount': amount,
            'payment_on_first_period': True,
            'rate': rate,
            'periods': periods,
            'leased_asset_account_id': self.asset_account.id,
            'short_term_loan_account_id': self.loan_account.id,
            'interest_expenses_account_id': self.interests_account.id,
            'product_id': self.product.id,
            'interests_product_id': self.interests_product.id,
            'partner_id': self.partner.id,
        })
        loan.compute_lines()
        return loan
