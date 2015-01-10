# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    account_asset_management tests
#
#    Copyright (c) 2014 ACSONE SA/NV (acsone.eu).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime

import openerp.tests.common as common

import time


class TestAssetManagement(common.TransactionCase):

    def setUp(self):
        super(TestAssetManagement, self).setUp()
        self.asset_model = self.registry('account.asset.asset')
        self.dl_model = self.registry('account.asset.depreciation.line')

    def test_1(self):
        """ Compute depreciation boards and post assets for first year,
            verify the depreciation values and values in parent assets. """
        #
        # first load demo assets and do some sanity checks
        #
        ict0 = self.browse_ref('account_asset_management.'
                               'account_asset_asset_ict0')
        self.assertEquals(ict0.state, 'draft')
        self.assertEquals(ict0.purchase_value, 1500)
        self.assertEquals(ict0.salvage_value, 0)
        self.assertEquals(ict0.asset_value, 1500)
        self.assertEquals(len(ict0.depreciation_line_ids), 1)
        vehicle0 = self.browse_ref('account_asset_management.'
                                   'account_asset_asset_vehicle0')
        self.assertEquals(vehicle0.state, 'draft')
        self.assertEquals(vehicle0.purchase_value, 12000)
        self.assertEquals(vehicle0.salvage_value, 2000)
        self.assertEquals(vehicle0.asset_value, 10000)
        self.assertEquals(len(vehicle0.depreciation_line_ids), 1)
        ict = self.browse_ref('account_asset_management.'
                              'account_asset_view_ict')
        # self.assertEquals(ict.purchase_value, 1500)
        # self.assertEquals(ict.salvage_value, 0)
        self.assertEquals(ict.asset_value, 1500)
        vehicle = self.browse_ref('account_asset_management.'
                                  'account_asset_view_vehicle')
        # self.assertEquals(vehicle.purchase_value, 12000)
        # self.assertEquals(vehicle.salvage_value, 2000)
        self.assertEquals(vehicle.asset_value, 10000)
        fa = self.browse_ref('account_asset_management.'
                             'account_asset_view_fa')
        # self.assertEquals(fa.purchase_value, 13500)
        # self.assertEquals(fa.salvage_value, 2000)
        self.assertEquals(fa.asset_value, 11500)

        #
        # compute depreciation boards
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
        # post first depreciation line
        #
        ict0.validate()
        ict0.depreciation_line_ids[1].create_move()
        ict0.refresh()
        self.assertEquals(ict0.state, 'open')
        self.assertEquals(ict0.value_depreciated, 500)
        self.assertEquals(ict0.value_residual, 1000)
        ict.refresh()
        self.assertEquals(ict.value_depreciated, 500)
        self.assertEquals(ict.value_residual, 1000)
        vehicle0.validate()
        vehicle0.depreciation_line_ids[1].create_move()
        vehicle0.refresh()
        self.assertEquals(vehicle0.state, 'open')
        self.assertEquals(vehicle0.value_depreciated, 2000)
        self.assertEquals(vehicle0.value_residual, 8000)
        vehicle.refresh()
        self.assertEquals(vehicle.value_depreciated, 2000)
        self.assertEquals(vehicle.value_residual, 8000)
        fa.refresh()
        self.assertEquals(fa.value_depreciated, 2500)
        self.assertEquals(fa.value_residual, 9000)

        #
        # change parent and check values
        #
        ict0.write({'parent_id': vehicle.id})
        ict.refresh()
        vehicle.refresh()
        fa.refresh()
        self.assertEquals(ict.value_depreciated, 0)
        self.assertEquals(ict.value_residual, 0)
        self.assertEquals(vehicle.value_depreciated, 2500)
        self.assertEquals(vehicle.value_residual, 9000)
        self.assertEquals(fa.value_depreciated, 2500)
        self.assertEquals(fa.value_residual, 9000)

    def test_2(self):
        """ prorata temporis depreciation """
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'category_id': self.ref('account_asset_management.'
                                    'account_asset_category_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
        asset = self.asset_model.browse(self.cr, self.uid, asset_id)
        self.asset_model.compute_depreciation_board(
            self.cr, self.uid, [asset.id])
        asset.refresh()
        self.assertEquals(asset.depreciation_line_ids[1].amount, 47.33)
        self.assertEquals(asset.depreciation_line_ids[2].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[3].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[4].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[5].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[6].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[-1].amount, 8.22)

    def test_3(self):
        """ prorata temporis depreciation with initial value in
            previous year """
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'category_id': self.ref('account_asset_management.'
                                    'account_asset_category_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': '%d-07-07' % (datetime.now().year - 1,),
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
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
        self.assertEquals(asset.value_depreciated, 325.08)
        self.assertEquals(asset.depreciation_line_ids[2].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[3].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[-1].amount, 8.22)

    def test_4(self):
        """ prorata temporis depreciation with initial value in
            curent year """
        asset_id = self.asset_model.create(self.cr, self.uid, {
            'name': 'test asset',
            'category_id': self.ref('account_asset_management.'
                                    'account_asset_category_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
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
        self.assertEquals(asset.value_depreciated, 279.44)
        self.assertEquals(asset.depreciation_line_ids[2].amount, 45.64)
        self.assertEquals(asset.depreciation_line_ids[3].amount, 55.55)
        self.assertEquals(asset.depreciation_line_ids[-1].amount, 8.22)
