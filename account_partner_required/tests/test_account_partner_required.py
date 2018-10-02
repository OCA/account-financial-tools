# -*- coding: utf-8 -*-
# Copyright 2014 Acsone (http://acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime

from openerp.tests import common
from openerp.exceptions import ValidationError


class TestAccountPartnerRequired(common.TransactionCase):

    def setUp(self):
        super(TestAccountPartnerRequired, self).setUp()
        self.account_obj = self.env['account.account']
        self.account_type_obj = self.env['account.account.type']
        self.move_obj = self.env['account.move']
        self.move_line_obj = self.env['account.move.line']

    def _create_move(self, with_partner, amount=100):
        date = datetime.now()
        period_id = self.env['account.period'].with_context(
            account_period_prefer_normal=True).find(date)[0]
        move_vals = {
            'journal_id': self.ref('account.sales_journal'),
            'period_id': period_id,
            'date': date,
        }
        move_id = self.move_obj.create(move_vals)
        self.move_line_obj.create({
            'move_id': move_id,
            'name': '/',
            'debit': 0,
            'credit': amount,
            'account_id': self.ref('account.a_sale')})
        move_line_id = self.move_line_obj.create({
            'move_id': move_id,
            'name': '/',
            'debit': amount,
            'credit': 0,
            'account_id': self.ref('account.a_recv'),
            'partner_id': self.ref('base.res_partner_1') if
            with_partner else False})
        return move_line_id

    def _set_partner_policy(self, policy, aref='account.a_recv'):
        account_type = self.ref(aref).user_type
        account_type.write({'partner_policy': policy})

    def test_optional(self):
        self._create_move(with_partner=False)
        self._create_move(with_partner=True)

    def test_always_no_partner(self):
        self._set_partner_policy('always')
        with self.assertRaises(ValidationError):
            self._create_move(with_partner=False)

    def test_always_no_partner_0(self):
        # accept missing partner when debit=credit=0
        self._set_partner_policy('always')
        self._create_move(with_partner=False, amount=0)

    def test_always_with_partner(self):
        self._set_partner_policy('always')
        self._create_move(with_partner=True)

    def test_never_no_partner(self):
        self._set_partner_policy('never')
        self._create_move(with_partner=False)

    def test_never_with_partner(self):
        self._set_partner_policy('never')
        with self.assertRaises(ValidationError):
            self._create_move(with_partner=True)

    def test_never_with_partner_0(self):
        # accept partner when debit=credit=0
        self._set_partner_policy('never')
        self._create_move(with_partner=True, amount=0)

    def test_always_remove_partner(self):
        # remove partner when policy is always
        self._set_partner_policy('always')
        line_id = self._create_move(with_partner=True)
        with self.assertRaises(ValidationError):
            line_id.write({'partner_id': False})

    def test_change_account(self):
        self._set_partner_policy('always', aref='account.a_pay')
        line_id = self._create_move(with_partner=False)
        # change account to a_pay with policy always but missing partner
        with self.assertRaises(ValidationError):
            line_id.write({'account_id': self.ref('account.a_pay')})
        # change account to a_pay with policy always with partner -> ok
        line_id.write({
            'account_id': self.ref('account.a_pay'),
            'partner_id': self.ref('base.res_partner_1'),
        })
