# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAccountTypeInactive(TransactionCase):

    def setUp(self):
        super(TestAccountTypeInactive, self).setUp()

        self.income_type = self.env.ref('account.data_account_type_revenue')
        self.payable_type = self.env.ref('account.data_account_type_payable')
        self.custom_type = self.env['account.account.type'].create({
            'name': 'Custom',
            'type': 'other'
        })

        self.journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'sale',
        })
        self.account_income = self.env['account.account'].create({
            'name': 'Test income',
            'code': 'REV',
            'user_type_id': self.income_type.id
        })
        self.account_payable = self.env['account.account'].create({
            'name': 'Test payable',
            'code': 'PAY',
            'reconcile': True,
            'user_type_id': self.payable_type.id
        })

    def test_inactive(self):

        self.custom_type.active = False
        # Check inactive account doesn't appear in search
        active_types = self.env['account.account.type'].search([])
        self.assertNotIn(self.custom_type, active_types)
        self.custom_type.active = True

        # Create move
        self.env['account.move'].create({
            'journal_id': self.journal.id,
            'line_ids': [(0, 0, {
                'name': 'debit payable',
                'debit': 20,
                'credit': 0,
                'account_id': self.account_payable.id,
            }), (0, 0, {
                'name': 'credit income',
                'debit': 0,
                'credit': 20,
                'account_id': self.account_income.id,
            })]
        })

        with self.assertRaises(ValidationError):
            self.income_type.active = False

        income_accounts = self.env['account.account'].search([
            ('user_type_id', '=', self.income_type.id)])

        income_accounts.write({
            'user_type_id': self.custom_type.id
        })

        self.income_type.active = False
        self.assertFalse(self.income_type.active)
