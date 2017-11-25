# -*- coding: utf-8 -*-
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import common


class TestAccountAsset(common.TransactionCase):
    def setUp(self):
        super(TestAccountAsset, self).setUp()
        # Create a journal for assets
        self.journal_asset = self.env['account.journal'].create({
            'name': 'Asset journal',
            'code': 'JRNL',
            'type': 'general',
            'update_posted': True,
        })
        # Create an account for assets
        self.account_asset = self.env['account.account'].create({
            'name': 'Asset',
            'code': '216x',
            'user_type_id': (
                self.env.ref('account.data_account_type_fixed_assets').id
            ),
        })
        # Create an account for assets depreciation
        self.account_asset_depreciation = self.env['account.account'].create({
            'name': 'Asset depreciation',
            'code': '2816x',
            'user_type_id': (
                self.env.ref('account.data_account_type_fixed_assets').id
            ),
        })
        # Create an account for assets expense
        self.account_asset_expense = self.env['account.account'].create({
            'name': 'Asset expense',
            'code': '681x',
            'user_type_id': (
                self.env.ref('account.data_account_type_expenses').id
            ),
        })
        # Create an account for assets loss
        self.account_asset_loss = self.env['account.account'].create({
            'name': 'Asset loss',
            'code': '671x',
            'user_type_id': (
                self.env.ref('account.data_account_type_expenses').id
            ),
        })
        # Create an asset category
        self.asset_category = self.env['account.asset.category'].create({
            'name': 'Asset category for testing',
            'journal_id': self.journal_asset.id,
            'account_asset_id': self.account_asset.id,
            'account_depreciation_id': self.account_asset_depreciation.id,
            'account_depreciation_expense_id': self.account_asset_expense.id,
            'account_loss_id': self.account_asset_loss.id,
        })
        # Create an invoice
        self.asset = self.env['account.asset.asset'].create({
            'name': 'Test Asset',
            'value': 100.00,
            'category_id': self.asset_category.id,
            'method_number': 10,
        })
        self.asset.validate()

    def test_asset_disposal(self):
        self.assertEqual(len(self.asset.depreciation_line_ids), 10)
        # Depreciate the first line
        self.asset.depreciation_line_ids[0].create_move()
        # Dispose asset
        disposal_date = fields.Date.today()
        wizard = self.env['account.asset.disposal.wizard'].with_context(
            active_ids=self.asset.ids, active_id=self.asset.id,
        ).create({
            'disposal_date': disposal_date,
        })
        self.assertEqual(wizard.loss_account_id, self.account_asset_loss)
        wizard.action_dispose()
        self.assertEqual(self.asset.disposal_date, disposal_date)
        self.assertEqual(self.asset.state, 'disposed')
        self.assertEqual(len(self.asset.depreciation_line_ids), 2)
        self.assertTrue(self.asset.disposal_move_id)
        self.assertEqual('posted', self.asset.disposal_move_id.state)
        self.assertEqual(self.asset.value, self.asset.disposal_move_id.amount)
        self.asset.action_disposal_undo()
        self.assertEqual(self.asset.state, 'open')
        self.assertEqual(len(self.asset.depreciation_line_ids), 10)
