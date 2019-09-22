# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import timedelta

import odoo.tests.common as common
from odoo import fields, _


class TestAccountBalanceProgressive(common.TransactionCase):

    def setUp(self):
        super(TestAccountBalanceProgressive, self).setUp()
        self.miscellaneous_journal = self.env['account.journal'].create({
            'name': 'Miscellaneus journal',
            'type': 'general',
            'code': 'OTHER',
        })
        self.account = self.env['account.account'].create({
            'code': 'TEST_CREDIT_PROGRESSIVE',
            'name': 'Credit progressive',
            'user_type_id': self.env.ref(
                'account.data_account_type_payable').id,
            'reconcile': True,
        })
        self.account_expenses = self.env['account.account'].create({
            'code': 'TEST_EXPENSE_PROGRESSIVE',
            'name': 'Expense progressive',
            'user_type_id': self.env.ref(
                'account.data_account_type_expenses').id,
        })

    def create_move(self, date, debit, credit):
        move = self.env['account.move'].create({
            'name': _('Account move'),
            'journal_id': self.miscellaneous_journal.id,
            'date': date,
            'line_ids': [
                (0, 0, {
                    'account_id': self.account.id,
                    'partner_id': self.env.ref('base.res_partner_12').id,
                    'debit': debit,
                    'credit': credit,
                    'name': 'Test move line',
                    'currency_id': self.ref('base.EUR'),
                }),
                (0, 0, {
                    'account_id': self.account_expenses.id,
                    'debit': credit,
                    'credit': debit,
                    'name': 'Test move line',
                    'currency_id': self.ref('base.EUR'),
                }),
            ]
        })
        return move

    def test_account_move(self):
        date = fields.Datetime.to_string(
            fields.Datetime.today() - timedelta(days=50))
        move = self.create_move(date, debit=50, credit=0)
        move.action_post()
        self.assertAlmostEqual(
            move.line_ids.filtered(
                lambda x: x.account_id == self.account
            ).balance_progressive, 50)
        date = fields.Datetime.to_string(
            fields.Datetime.today() - timedelta(days=30))
        move1 = self.create_move(date, debit=0, credit=15)
        move1.action_post()
        self.assertAlmostEqual(
            move1.line_ids.filtered(
                lambda x: x.account_id == self.account
            ).balance_progressive, 35)
        date = fields.Datetime.to_string(fields.Datetime.today())
        move2 = self.create_move(date, debit=0, credit=30)
        move2.action_post()
        self.assertAlmostEqual(
            move2.line_ids.filtered(
                lambda x: x.account_id == self.account
            ).balance_progressive, 5)
        self.assertAlmostEqual(
            move2.line_ids.filtered(
                lambda x: x.account_id == self.account_expenses
            ).balance_progressive, -5)
