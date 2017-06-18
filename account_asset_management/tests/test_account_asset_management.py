# -*- coding: utf-8 -*-
# Copyright (c) 2014 ACSONE SA/NV (acsone.eu).
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
from datetime import date, datetime
import time

import openerp.tests.common as common


class TestAssetManagement(common.TransactionCase):

    def setUp(self):
        super(TestAssetManagement, self).setUp()
        self.asset_model = self.registry('account.asset')
        self.dl_model = self.registry('account.asset.line')

    def test_1_nonprorata_basic(self):
        """Basic tests of depreciation board computations and postings."""
        #
        # first load demo assets and do some sanity checks
        #
        ict0 = self.browse_ref('account_asset_management.'
                               'account_asset_asset_ict0')
        self.assertEquals(ict0.state, 'draft')
        self.assertEquals(ict0.purchase_value, 1500)
        self.assertEquals(ict0.salvage_value, 0)
        self.assertEquals(ict0.depreciation_base, 1500)
        self.assertEquals(len(ict0.depreciation_line_ids), 1)
        vehicle0 = self.browse_ref('account_asset_management.'
                                   'account_asset_asset_vehicle0')
        self.assertEquals(vehicle0.state, 'draft')
        self.assertEquals(vehicle0.purchase_value, 12000)
        self.assertEquals(vehicle0.salvage_value, 2000)
        self.assertEquals(vehicle0.depreciation_base, 10000)
        self.assertEquals(len(vehicle0.depreciation_line_ids), 1)

        #
        # I compute the depreciation boards
        #
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [ict0.id, vehicle0.id])
        ict0.refresh()
        self.assertEquals(len(ict0.depreciation_line_ids), 4)
        self.assertEquals(ict0.depreciation_line_ids[1].amount, 500)
        vehicle0.refresh()
        self.assertEquals(len(vehicle0.depreciation_line_ids), 6)
        self.assertEquals(vehicle0.depreciation_line_ids[1].amount, 2000)

        #
        # I post the first depreciation line
        #
        ict0.validate()
        ict0.depreciation_line_ids[1].create_move()
        ict0.refresh()
        self.assertEquals(ict0.state, 'open')
        self.assertEquals(ict0.value_depreciated, 500)
        self.assertEquals(ict0.value_residual, 1000)
        vehicle0.validate()
        vehicle0.depreciation_line_ids[1].create_move()
        vehicle0.refresh()
        self.assertEquals(vehicle0.state, 'open')
        self.assertEquals(vehicle0.value_depreciated, 2000)
        self.assertEquals(vehicle0.value_residual, 8000)

    def test_2_prorata_basic(self):
        """Prorata temporis depreciation basic test."""
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                                   46.44, places=2)
        else:
            self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                                   47.33, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[4].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[5].amount,
                               55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[6].amount,
                               55.55, places=2)
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                                   9.11, places=2)
        else:
            self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                                   8.22, places=2)

    def test_3_proprata_init_prev_year(self):
        """Prorata temporis depreciation with init value in prev year."""
        # I create an asset in current year
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': '%d-07-07' % (datetime.now().year - 1,),
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
        # I create a initial depreciation line in previous year
        self.dl_model.create(self.cr, self.uid, {
            'asset_id': asset_id,
            'amount': 325.08,
            'line_date': '%d-12-31' % (datetime.now().year - 1,),
            'type': 'depreciate',
            'init_entry': True,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.assertEquals(len(asset.depreciation_line_ids), 2)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()
        # I check the depreciated value is the initial value
        self.assertAlmostEqual(asset.value_depreciated, 325.08,
                               places=2)
        # I check computed values in the depreciation board
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 55.55,
                               places=2)
        if calendar.isleap(date.today().year - 1):
            # for leap years the first year depreciation amount of 325.08
            # is too high and hence a correction is applied to the next
            # entry of the table
            self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                                   54.66, places=2)
            self.assertAlmostEqual(asset.depreciation_line_ids[3].amount,
                                   55.55, places=2)
            self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                                   9.11, places=2)
        else:
            self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                                   55.55, places=2)
            self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                                   8.22, places=2)

    def test_4_prorata_init_cur_year(self):
        """Prorata temporis depreciation with init value in curent year."""
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
        self.dl_model.create(self.cr, self.uid, {
            'asset_id': asset_id,
            'amount': 279.44,
            'line_date': time.strftime('%Y-11-30'),
            'type': 'depreciate',
            'init_entry': True,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.assertEquals(len(asset.depreciation_line_ids), 2)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()
        # I check the depreciated value is the initial value
        self.assertAlmostEqual(asset.value_depreciated, 279.44,
                               places=2)
        # I check computed values in the depreciation board
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                                   44.75, places=2)
        else:
            self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                                   45.64, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount,
                               55.55, places=2)
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                                   9.11, places=2)
        else:
            self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                                   8.22, places=2)

    def test_5_degressive_linear(self):
        """Degressive-Linear with annual and quarterly depreciation."""

        # annual depreciation
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 1000,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_time': 'year',
            'method': 'degr-linear',
            'method_progress_factor': 0.40,
            'method_number': 5,
            'method_period': 'year',
            'prorata': False,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()

        # check values in the depreciation board
        self.assertEquals(len(asset.depreciation_line_ids), 5)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               400.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                               240.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount,
                               200.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[4].amount,
                               160.00, places=2)

        # quarterly depreciation
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 1000,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_time': 'year',
            'method': 'degr-linear',
            'method_progress_factor': 0.40,
            'method_number': 5,
            'method_period': 'quarter',
            'prorata': False,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()

        # check values in the depreciation board
        self.assertEquals(len(asset.depreciation_line_ids), 15)
        # lines prior to asset start period are grouped in the first entry
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               300.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount,
                               60.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[7].amount,
                               50.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[13].amount,
                               40.00, places=2)

    def test_6_degressive_limit(self):
        """Degressive with annual depreciation."""
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 1000,
            'salvage_value': 100,
            'date_start': time.strftime('%Y-07-07'),
            'method_time': 'year',
            'method': 'degr-limit',
            'method_progress_factor': 0.40,
            'method_number': 5,
            'method_period': 'year',
            'prorata': False,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()

        # check values in the depreciation board
        self.assertEquals(len(asset.depreciation_line_ids), 6)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               400.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                               240.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount,
                               144.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[4].amount,
                               86.40, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[5].amount,
                               29.60, places=2)

    def test_7_linear_limit(self):
        """Degressive with annual depreciation."""
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 1000,
            'salvage_value': 100,
            'date_start': time.strftime('%Y-07-07'),
            'method_time': 'year',
            'method': 'linear-limit',
            'method_number': 5,
            'method_period': 'year',
            'prorata': False,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()

        # check values in the depreciation board
        self.assertEquals(len(asset.depreciation_line_ids), 6)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               200.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                               100.00, places=2)
