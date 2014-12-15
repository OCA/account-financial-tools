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

import openerp.tests.common as common


class TestAssetManagement(common.TransactionCase):

    def setUp(self):
        super(TestAssetManagement, self).setUp()
        self.asset_model = self.registry('account.asset.asset')

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
