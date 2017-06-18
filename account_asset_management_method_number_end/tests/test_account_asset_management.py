# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

import openerp.tests.common as common


class TestAssetManagement(common.TransactionCase):

    def setUp(self):
        super(TestAssetManagement, self).setUp()
        self.asset_model = self.registry('account.asset')
        self.dl_model = self.registry('account.asset.line')

    def test_1_linear_number(self):
        """Linear with Method Time 'Number'."""
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 1000,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_time': 'number',
            'method': 'linear',
            'method_number': 12,
            'method_period': 'month',
            'prorata': True,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()

        # check values in the depreciation board
        self.assertEquals(len(asset.depreciation_line_ids), 13)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               83.33, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                               83.37, places=2)

    def test_2_linear_end(self):
        """Linear with Method Time End Date."""
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 1000,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-01-30'),
            'method_time': 'end',
            'method': 'linear',
            'method_end': time.strftime('%Y-06-30'),
            'method_period': 'month',
            'prorata': True,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()

        # check values in the depreciation board
        self.assertEquals(len(asset.depreciation_line_ids), 7)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               166.67, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                               166.65, places=2)
