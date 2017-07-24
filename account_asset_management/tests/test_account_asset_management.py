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

import odoo.tests.common as common
from odoo import tools
from odoo.modules.module import get_resource_path

import time


class TestAssetManagement(common.TransactionCase):

    def _load(self, module, *args):
        tools.convert_file(self.cr, module,
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           self.registry._assertion_report)

    def setUp(self):
        super(TestAssetManagement, self).setUp()
        self.asset_model = self.env['account.asset']
        self.dl_model = self.env['account.asset.line']
        self._load('account', 'test', 'account_minimal_test.xml')
        self._load('account_asset_management', 'demo',
                   'account_asset_demo.xml')
        # ENVIRONEMENTS

        self.account_invoice = self.env['account.invoice']
        self.account_move_line = self.env['account.move.line']
        self.account_account = self.env['account.account']
        self.account_journal = self.env['account.journal']
        self.account_invoice_line = self.env['account.invoice.line']

        # INSTANCES

        # Instance: company
        self.company = self.env.ref('base.main_company')

        # Instance: account type (receivable)
        self.type_recv = self.env.ref('account.data_account_type_receivable')

        # Instance: account type (payable)
        self.type_payable = self.env.ref('account.data_account_type_payable')

        # Instance: account (receivable)
        self.account_recv = self.account_account.create({
            'name': 'test_account_receivable',
            'code': '123',
            'user_type_id': self.type_recv.id,
            'company_id': self.company.id,
            'reconcile': True})

        # Instance: account (payable)
        self.account_payable = self.account_account.create({
            'name': 'test_account_payable',
            'code': '321',
            'user_type_id': self.type_payable.id,
            'company_id': self.company.id,
            'reconcile': True})

        # Instance: partner
        self.partner = self.env.ref('base.res_partner_2')

        # Instance: journal
        self.journal = self.account_journal.search([('code', '=', 'BILL')])

        # Instance: product
        self.product = self.env.ref('product.product_product_4')

        # Instance: invoice line
        self.invoice_line = self.account_invoice_line.create({
            'name': 'test',
            'account_id': self.account_payable.id,
            'price_unit': 2000.00,
            'quantity': 1,
            'product_id': self.product.id})

        # Instance: invoice
        self.invoice = self.account_invoice.create({
            'partner_id': self.partner.id,
            'account_id': self.account_recv.id,
            'payment_term': False,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(4, self.invoice_line.id)]})

    def test_0(self):
        asset01 = self.env.ref(
            "account_asset_management.account_asset_vehicle0")
        asset01.validate()
        self.assertEqual(asset01.state, 'open')
        asset01.compute_depreciation_board()
        self.assertTrue(asset01.method_number ==
                        (len(asset01.depreciation_line_ids) - 1))
        dl = self.dl_model.search([('asset_id', '=', asset01.id),
                                   ('type', '=', 'depreciate')], limit=1)
        dl.create_move()

    def test_1_hierarchy(self):
        """Test computations across the asset hierarchy."""
        #
        # first load demo assets and do some sanity checks
        #
        ict0 = self.env.ref('account_asset_management.account_asset_ict0')
        self.assertEquals(ict0.state, 'draft')
        self.assertEquals(ict0.purchase_value, 1500)
        self.assertEquals(ict0.salvage_value, 0)
        self.assertEquals(ict0.depreciation_base, 1500)
        self.assertEquals(len(ict0.depreciation_line_ids), 1)
        vehicle0 = self.env.ref('account_asset_management.'
                                'account_asset_vehicle0')
        self.assertEquals(vehicle0.state, 'draft')
        self.assertEquals(vehicle0.purchase_value, 12000)
        self.assertEquals(vehicle0.salvage_value, 2000)
        self.assertEquals(vehicle0.depreciation_base, 10000)
        self.assertEquals(len(vehicle0.depreciation_line_ids), 1)
        ict = self.env.ref('account_asset_management.'
                           'account_asset_view_ict')
        # self.assertEquals(ict.purchase_value, 1500)
        # self.assertEquals(ict.salvage_value, 0)
        self.assertEquals(ict.depreciation_base, 1500)
        vehicle = self.env.ref('account_asset_management.'
                               'account_asset_view_vehicle')
        # self.assertEquals(vehicle.purchase_value, 12000)
        # self.assertEquals(vehicle.salvage_value, 2000)
        self.assertEquals(vehicle.depreciation_base, 10000)
        fa = self.env.ref('account_asset_management.'
                          'account_asset_view_fa')
        # self.assertEquals(fa.purchase_value, 13500)
        # self.assertEquals(fa.salvage_value, 2000)
        self.assertEquals(fa.depreciation_base, 11500)

        #
        # I compute the depreciation boards
        #
        ict0.compute_depreciation_board()
        vehicle0.compute_depreciation_board()
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
        # I change the parent and check values
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

    def test_2_prorata_basic(self):
        """Prorata temporis depreciation basic test."""
        asset = self.asset_model.create({
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
        asset.compute_depreciation_board()
        asset.refresh()
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount, 47.33,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[4].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[5].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[6].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount, 8.22,
                               places=2)

    def test_3_proprata_init_prev_year(self):
        """Prorata temporis depreciation with init value in prev year."""
        # I create an asset in current year
        asset = self.asset_model.create({
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': '%d-07-07' % (datetime.now().year - 1,),
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
        # I create a initial depreciation line in previous year
        self.dl_model.create({
            'asset_id': asset.id,
            'amount': 325.08,
            'line_date': '%d-12-31' % (datetime.now().year - 1,),
            'type': 'depreciate',
            'init_entry': True,
        })
        self.assertEquals(len(asset.depreciation_line_ids), 2)
        asset.compute_depreciation_board()
        asset.refresh()
        # I check the depreciated value is the initial value
        self.assertAlmostEqual(asset.value_depreciated, 325.08,
                               places=2)
        # I check computed values in the depreciation board
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount, 8.22,
                               places=2)

    def test_4_prorata_init_cur_year(self):
        """Prorata temporis depreciation with init value in curent year."""
        asset = self.asset_model.create({
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-07-07'),
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
        })
        self.dl_model.create({
            'asset_id': asset.id,
            'amount': 279.44,
            'line_date': time.strftime('%Y-11-30'),
            'type': 'depreciate',
            'init_entry': True,
        })
        self.assertEquals(len(asset.depreciation_line_ids), 2)
        asset.compute_depreciation_board()
        asset.refresh()
        # I check the depreciated value is the initial value
        self.assertAlmostEqual(asset.value_depreciated, 279.44,
                               places=2)
        # I check computed values in the depreciation board
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount, 45.64,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 55.55,
                               places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount, 8.22,
                               places=2)

    def test_5_asset_from_invoice(self):
        all_asset = self.env['account.asset'].search([])
        invoice = self.invoice
        asset_profile = self.env.ref(
            'account_asset_management.account_asset_profile_car_5Y')
        asset_profile.asset_product_item = False
        self.assertTrue(len(invoice.invoice_line_ids) > 0)
        line = invoice.invoice_line_ids[0]
        self.assertTrue(line.price_unit > 0.0)
        line.quantity = 2
        line.asset_profile_id = asset_profile
        invoice.action_invoice_open()
        # I get all asset after invoice validation
        current_asset = self.env['account.asset'].search([])
        # I get the new asset
        new_asset = current_asset - all_asset
        # I check that a new asset is created
        self.assertEqual(len(new_asset), 1)
        # I check that the new asset has the correct purchase value
        self.assertAlmostEqual(new_asset.purchase_value,
                               -line.price_unit * line.quantity,
                               places=2)

    def test_6_asset_from_invoice_product_item(self):
        all_asset = self.env['account.asset'].search([])
        invoice = self.invoice
        asset_profile = self.env.ref(
            'account_asset_management.account_asset_profile_car_5Y')
        asset_profile.asset_product_item = True
        self.assertTrue(len(invoice.invoice_line_ids) > 0)
        line = invoice.invoice_line_ids[0]
        self.assertTrue(line.price_unit > 0.0)
        line.quantity = 2
        line.asset_profile_id = asset_profile
        invoice.action_invoice_open()
        # I get all asset after invoice validation
        current_asset = self.env['account.asset'].search([])
        # I get the new asset
        new_asset = current_asset - all_asset
        # I check that a new asset is created
        self.assertEqual(len(new_asset), line.quantity)
        for asset in new_asset:
            # I check that the new asset has the correct purchase value
            self.assertAlmostEqual(
                asset.purchase_value, -line.price_unit, places=2)
