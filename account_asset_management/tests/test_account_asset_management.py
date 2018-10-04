# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV <https://acsone.eu>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import calendar
from datetime import date, datetime

import openerp.tests.common as common

import time


class TestAssetManagement(common.TransactionCase):

    post_install = True

    def setUp(self):
        super(TestAssetManagement, self).setUp()
        self.asset_model = self.env['account.asset.asset']
        self.dl_model = self.env['account.asset.depreciation.line']

    def test_0_process(self):
        vehicle0 = self.env.ref(
            'account_asset_management.account_asset_asset_vehicle0')
        vehicle0.validate()
        self.assertEquals(vehicle0.state, 'open')

        vehicle0.compute_depreciation_board()
        self.assertEquals(
            vehicle0.method_number, len(vehicle0.depreciation_line_ids) - 1)

        self.dl_model.search([
            ('asset_id', '=', vehicle0.id),
            ('type', '=', 'depreciate')],
            limit=1).create_move()

    def test_1_hierarchy(self):
        """Test computations across the asset hierarchy."""
        #
        # first load demo assets and do some sanity checks
        #
        ict0 = self.env.ref(
            'account_asset_management.account_asset_asset_ict0')
        self.assertEquals(ict0.state, 'draft')
        self.assertEquals(ict0.purchase_value, 1500)
        self.assertEquals(ict0.salvage_value, 0)
        self.assertEquals(ict0.asset_value, 1500)
        self.assertEquals(len(ict0.depreciation_line_ids), 1)
        vehicle0 = self.env.ref(
            'account_asset_management.account_asset_asset_vehicle0')
        self.assertEquals(vehicle0.state, 'draft')
        self.assertEquals(vehicle0.purchase_value, 12000)
        self.assertEquals(vehicle0.salvage_value, 2000)
        self.assertEquals(vehicle0.asset_value, 10000)
        self.assertEquals(len(vehicle0.depreciation_line_ids), 1)
        ict = self.env.ref('account_asset_management.account_asset_view_ict')
        self.assertEquals(ict.asset_value, 1500)
        vehicle = self.env.ref(
            'account_asset_management.account_asset_view_vehicle')
        self.assertEquals(vehicle.asset_value, 10000)
        fa = self.env.ref('account_asset_management.account_asset_view_fa')
        self.assertEquals(fa.asset_value, 11500)

        #
        # I compute the depreciation boards
        #
        (ict0 + vehicle0).compute_depreciation_board()
        self.assertEquals(len(ict0.depreciation_line_ids), 4)
        self.assertEquals(ict0.depreciation_line_ids[1].amount, 500)
        self.assertEquals(len(vehicle0.depreciation_line_ids), 6)
        self.assertEquals(vehicle0.depreciation_line_ids[1].amount, 2000)

        #
        # I post the first depreciation line
        #
        ict0.validate()
        ict0.depreciation_line_ids[1].create_move()
        self.assertEquals(ict0.state, 'open')
        self.assertEquals(ict0.value_depreciated, 500)
        self.assertEquals(ict0.value_residual, 1000)
        self.assertEquals(ict.value_depreciated, 500)
        self.assertEquals(ict.value_residual, 1000)
        vehicle0.validate()
        vehicle0.depreciation_line_ids[1].create_move()
        self.assertEquals(vehicle0.state, 'open')
        self.assertEquals(vehicle0.value_depreciated, 2000)
        self.assertEquals(vehicle0.value_residual, 8000)
        self.assertEquals(vehicle.value_depreciated, 2000)
        self.assertEquals(vehicle.value_residual, 8000)
        self.assertEquals(fa.value_depreciated, 2500)
        self.assertEquals(fa.value_residual, 9000)

        #
        # I change the parent and check values
        #
        ict0.write({'parent_id': vehicle.id})
        self.assertEquals(ict.value_depreciated, 0)
        self.assertEquals(ict.value_residual, 0)
        self.assertEquals(vehicle.value_depreciated, 2500)
        self.assertEquals(vehicle.value_residual, 9000)
        self.assertEquals(fa.value_depreciated, 2500)
        self.assertEquals(fa.value_residual, 9000)

    def test_2_prorata_basic(self):
        """Prorata temporis depreciation basic test."""
        asset_id = self.asset_model.create({
            'name': 'test asset',
            'category_id': self.ref(
                'account_asset_management.account_asset_category_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method': 'linear',
            'method_number': 5,
            'method_time': 'year',
            'method_period': 'month',
            'prorata': True,
        })
        asset_id.compute_depreciation_board()
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset_id.depreciation_line_ids[1].amount,
                                   46.44, places=2)
        else:
            self.assertAlmostEqual(asset_id.depreciation_line_ids[1].amount,
                                   47.33, places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[2].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[3].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[4].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[5].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[6].amount,
                               55.55, places=2)
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset_id.depreciation_line_ids[-1].amount,
                                   9.11, places=2)
        else:
            self.assertAlmostEqual(asset_id.depreciation_line_ids[-1].amount,
                                   8.22, places=2)

    def test_3_proprata_init_prev_year(self):
        """Prorata temporis depreciation with init value in prev year."""
        # I create an asset in current year
        asset_id = self.asset_model.create({
            'name': 'test asset',
            'category_id': self.ref('account_asset_management.'
                                    'account_asset_category_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': '%d-07-07' % (datetime.now().year - 1,),
            'method_number': 5,
            'method_period': 'month',
            'method': 'linear',
            'method_time': 'year',
            'prorata': True,
        })
        # I create a initial depreciation line in previous year
        self.dl_model.create({
            'asset_id': asset_id.id,
            'amount': 325.08,
            'line_date': '%d-12-31' % (datetime.now().year - 1,),
            'type': 'depreciate',
            'init_entry': True,
        })
        self.assertEquals(len(asset_id.depreciation_line_ids), 2)
        asset_id.compute_depreciation_board()
        # I check the depreciated value is the initial value
        self.assertAlmostEqual(asset_id.value_depreciated, 325.08,
                               places=2)
        # I check computed values in the depreciation board
        self.assertAlmostEqual(asset_id.depreciation_line_ids[2].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[3].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[-1].amount, 8.22,
                               places=2)

    def test_4_prorata_init_cur_year(self):
        """Prorata temporis depreciation with init value in curent year."""
        asset_id = self.asset_model.create({
            'name': 'test asset',
            'category_id': self.ref(
                'account_asset_management.account_asset_category_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method': 'linear',
            'method_number': 5,
            'method_period': 'month',
            'method_time': 'year',
            'prorata': True,
        })
        self.dl_model.create({
            'asset_id': asset_id.id,
            'amount': 279.44,
            'line_date': time.strftime('%Y-11-30'),
            'type': 'depreciate',
            'init_entry': True,
        })
        self.assertEquals(len(asset_id.depreciation_line_ids), 2)
        asset_id.compute_depreciation_board()
        # I check the depreciated value is the initial value
        self.assertAlmostEqual(asset_id.value_depreciated, 279.44,
                               places=2)
        # I check computed values in the depreciation board
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset_id.depreciation_line_ids[2].amount,
                                   44.75, places=2)
        else:
            self.assertAlmostEqual(asset_id.depreciation_line_ids[2].amount,
                                   45.64, places=2)
        self.assertAlmostEqual(asset_id.depreciation_line_ids[3].amount,
                               55.55, places=2)
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset_id.depreciation_line_ids[-1].amount,
                                   9.11, places=2)
        else:
            self.assertAlmostEqual(asset_id.depreciation_line_ids[-1].amount,
                                   8.22, places=2)
