# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Luis M. Ontalba - <luis.martinez@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo.tests import common
from odoo import fields
from datetime import datetime


class TestAccountAssetDisposal(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountAssetDisposal, cls).setUpClass()
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test Journal',
            'type': 'general',
            'code': 'TJ',
            'update_posted': True,
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test Account Type',
        })
        cls.asset_account = cls.env['account.account'].create({
            'code': 'TAA',
            'name': 'Test Asset Account',
            'internal_type': 'other',
            'user_type_id': cls.account_type.id,
        })
        cls.asset_category_number = cls.env['account.asset.category'].create({
            'name': 'Test Category Number',
            'journal_id': cls.journal.id,
            'account_asset_id': cls.asset_account.id,
            'account_depreciation_id': cls.asset_account.id,
            'account_depreciation_expense_id': cls.asset_account.id,
            'method_time': 'number',
            'method_number': 10,
            'method_period': 12,
            'method': 'linear',
        })
        cls.asset = cls.env['account.asset.asset'].create({
            'name': 'Test Asset Number',
            'category_id': cls.asset_category_number.id,
            'value': 16000.0,
            'salvage_value': 1000.0,
            'method_number': 15,
        })
        cls.asset.validate()
        cls.date_time = fields.Date.to_string(datetime.now())

    def test_asset_depreciation_board(self):
        self.assertEqual(len(self.asset.depreciation_line_ids), 15)
        self.first_line = self.asset.depreciation_line_ids[0]
        self.assertEqual(self.first_line.depreciated_value, 1000.0)
        self.assertEqual(self.first_line.remaining_value, 14000.0)

    def test_asset_unamortized(self):
        self.asset.set_to_close()
        self.assertTrue(self.asset.disposal_move_id)
        self.assertEqual(self.asset.disposal_date, self.date_time)
        self.assertEqual(self.asset.state, 'disposed')
        self.asset.action_disposal_undo()
        self.assertEqual(self.asset.state, 'open')
        self.assertEqual(self.asset.method_end,
                         self.asset.category_id.method_end)
        self.assertEqual(self.asset.method_number,
                         self.asset.category_id.method_number)

    def test_asset_amortized(self):
        self.asset.depreciation_line_ids.create_move()
        self.asset.set_to_close()
        self.asset.action_disposal_undo()
        self.assertEqual(self.asset.state, 'close')
