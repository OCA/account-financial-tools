# -*- coding: utf-8 -*-
from datetime import date, datetime
from decimal import getcontext, Decimal

from openerp.tests.common import TransactionCase


class TestAccountMoveLine(TransactionCase):

    def setUp(self):
        super(TestAccountMoveLine, self).setUp()
        self.move_obj = self.env['account.move']
        self.move_line_obj = self.env['account.move.line']
        self.curr_obj = self.env['res.currency']
        self.currency_rate = 0.721700
        self._set_currency_rate('GBP', self.currency_rate)

    def _create_move(self):
        date = datetime.today()
        period = self.env['account.period'].with_context(
            {'account_period_prefer_normal': True}
        ).find(date)[0]
        move_vals = {
            'journal_id': self.ref('account.bank_journal'),
            'period_id': period.id,
            'date': date,
        }
        return self.move_obj.create(move_vals)

    def _create_move_line_debit(self, move_id, amount_currency):
        vals = {
            'move_id': move_id,
            'name': '/',
            'account_id': self.ref('account.bnk'),
            'currency_id': self.ref('base.GBP'),
            'amount_currency': amount_currency,
        }
        return self.move_line_obj.create(vals)

    def _create_move_line_credit(self, move_id, amount_currency):
        vals = {
            'move_id': move_id,
            'name': '/',
            'account_id': self.ref('account.a_pay'),
            'currency_id': self.ref('base.GBP'),
            'amount_currency': -amount_currency,
        }
        return self.move_line_obj.create(vals)

    def _set_currency_rate(self, currency_name, rate):
        company_currency_id = self.env.user.company_id.currency_id.id
        eur_currency_id = self.ref('base.EUR')
        self.assertEqual(company_currency_id, eur_currency_id)
        currency = self.curr_obj.search(
            [('name', '=', currency_name)]
        )[0]
        self.env['res.currency.rate'].create(
            {
                'name': date.fromordinal(date.today().toordinal() - 1),
                'currency_id': currency.id,
                'rate': rate,
            }
        )

    def assert_debit_and_credit(
            self, move_line_debit, move_line_credit, amount_currency
    ):
        getcontext().prec = 2
        debit = move_line_debit.debit
        credit = move_line_credit.credit
        self.assertEqual(
            (Decimal(debit) / Decimal(
                1 / self.currency_rate * amount_currency
            )),
            Decimal(1.0)
        )
        self.assertEqual(
            (Decimal(credit) / Decimal(
                1 / self.currency_rate * amount_currency)
             ),
            Decimal(1.0)
        )

    def _create_move_lines(self, amount_currency):
        move_id = self._create_move().id
        move_line_debit = self._create_move_line_debit(
            move_id, amount_currency
        )
        move_line_credit = self._create_move_line_credit(
            move_id, amount_currency
        )
        return move_line_debit, move_line_credit

    def _update_move_lines(
            self, move_line_debit, move_line_credit, new_amount_currency
    ):
        move_line_debit.write(
            {'amount_currency': new_amount_currency}
        )
        move_line_credit.write(
            {'amount_currency': -new_amount_currency}
        )

    def test_account_move_line_create(self):
        amount_currency = 1775
        move_line_debit, move_line_credit = self._create_move_lines(
            amount_currency
        )
        self.assert_debit_and_credit(
            move_line_debit, move_line_credit, amount_currency
        )

    def test_account_move_line_write(self):
        amount_currency = 1775
        move_line_debit, move_line_credit = self._create_move_lines(
            amount_currency
        )
        new_amount_currency = 1785.97
        self._update_move_lines(
            move_line_debit, move_line_credit, new_amount_currency
        )
        self.assert_debit_and_credit(
            move_line_debit, move_line_credit, new_amount_currency
        )

    def test_account_move_line_onchange_currency(self):
        amount_currency = 305.33
        move_id = self._create_move().id
        move_line_debit = self._create_move_line_debit(
            move_id, amount_currency
        )
        move_line_debit._onchange_currency()
        # how do we test an onchange?
