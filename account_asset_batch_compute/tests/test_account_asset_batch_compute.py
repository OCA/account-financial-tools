# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp.addons.connector.tests.common import mock_job_delay_to_direct
from datetime import date

DELAY2 = ('openerp.addons.account_asset_batch_compute.wizards.'
          'asset_depreciation_confirmation_wizard.async_asset_compute')
DELAY1 = ('openerp.addons.account_asset_batch_compute.models.'
          'account_asset_asset.async_compute_entries')


class TestAccountAssetBatchCompute(TransactionCase):

    def setUp(self):
        super(TestAccountAssetBatchCompute, self).setUp()
        self.wiz_obj = self.env['asset.depreciation.confirmation.wizard']
        self.asset01 = self.env.ref(
            'account_asset_management.account_asset_asset_ict0')
        self.asset01.method_period = 'month'
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        self.asset01.date_start = first_day_of_month

    def test_1(self):
        period = self.env['account.period'].find()
        wiz = self.wiz_obj.create({'batch_processing': False,
                                   'period_id': period.id})
        # I check if this asset is draft
        self.assertEqual(self.asset01.state, 'draft')
        # I confirm this asset
        self.asset01.validate()
        # I check if this asset is running
        self.assertEqual(self.asset01.state, 'open')
        self.asset01.compute_depreciation_board()
        # I check that there is no depreciation line
        depreciation_line = self.asset01.depreciation_line_ids\
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 0)
        wiz.asset_compute()
        depreciation_line = self.asset01.depreciation_line_ids\
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 1)

    def test_2(self):
        period = self.env['account.period'].find()
        wiz = self.wiz_obj.create({'batch_processing': True,
                                   'period_id': period.id})
        # I check if this asset is draft
        self.assertEqual(self.asset01.state, 'draft')
        # I confirm this asset
        self.asset01.validate()
        # I check if this asset is running
        self.assertEqual(self.asset01.state, 'open')
        self.asset01.compute_depreciation_board()
        # I check that there is no depreciation line
        depreciation_line = self.asset01.depreciation_line_ids\
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 0)
        with mock_job_delay_to_direct(DELAY1),\
                mock_job_delay_to_direct(DELAY2):
            wiz.asset_compute()
        depreciation_line = self.asset01.depreciation_line_ids\
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 1)
