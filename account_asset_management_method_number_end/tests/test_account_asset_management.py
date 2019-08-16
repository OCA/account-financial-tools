# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo.tests.common import SavepointCase
from odoo import tools
from odoo.modules.module import get_resource_path


class TestAssetManagement(SavepointCase):

    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(cls.cr, module,
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           cls.registry._assertion_report)

    @classmethod
    def setUpClass(cls):
        super(TestAssetManagement, cls).setUpClass()

        cls._load('account', 'test', 'account_minimal_test.xml')
        cls._load('account_asset_management', 'tests',
                  'account_asset_test_data.xml')

        cls.asset_model = cls.env['account.asset']
        cls.dl_model = cls.env['account.asset.line']

    def test_1_linear_number(self):
        """Linear with Method Time 'Number'."""
        asset = self.asset_model.create({
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
        asset.compute_depreciation_board()
        asset.refresh()

        # check values in the depreciation board
        self.assertEqual(len(asset.depreciation_line_ids), 13)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               83.33, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                               83.37, places=2)

    def test_2_linear_end(self):
        """Linear with Method Time End Date."""
        asset = self.asset_model.create({
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
        asset.compute_depreciation_board()
        asset.refresh()

        # check values in the depreciation board
        self.assertEqual(len(asset.depreciation_line_ids), 7)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               166.67, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                               166.65, places=2)
