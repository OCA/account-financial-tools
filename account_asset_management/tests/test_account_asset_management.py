# -*- coding: utf-8 -*-
# Copyright (c) 2014 ACSONE SA/NV (acsone.eu).
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
from datetime import date, datetime
import time

import odoo.tests.common as common
from odoo import tools
from odoo.modules.module import get_resource_path


class TestAssetManagement(common.TransactionCase):

    def _load(self, module, *args):
        tools.convert_file(self.cr, module,
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           self.registry._assertion_report)

    def setUp(self):
        super(TestAssetManagement, self).setUp()

        self._load('account', 'test', 'account_minimal_test.xml')
        self._load('account_asset_management', 'tests',
                   'account_asset_test_data.xml')

        # ENVIRONEMENTS
        self.asset_model = self.env['account.asset']
        self.dl_model = self.env['account.asset.line']
        self.remove_model = self.env['account.asset.remove']
        self.account_invoice = self.env['account.invoice']
        self.account_move_line = self.env['account.move.line']
        self.account_account = self.env['account.account']
        self.account_journal = self.env['account.journal']
        self.account_invoice_line = self.env['account.invoice.line']

        # INSTANCES

        # Instance: company
        self.company = self.env.ref('base.main_company')

        # Instance: Account settings
        self.acs_model = self.env['account.config.settings']

        values = {'fiscalyear_lock_date': "%s-12-31" % (date.today().year - 2)}

        self.acs_model.create(values)

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
        self.journal = self.account_journal.search(
            [('type', '=', 'purchase')])[0]

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
            'journal_id': self.journal.id,
            'invoice_line_ids': [(4, self.invoice_line.id)]})

    def test_01_nonprorata_basic(self):
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
        ict0.compute_depreciation_board()
        ict0.refresh()
        self.assertEquals(len(ict0.depreciation_line_ids), 4)
        self.assertEquals(ict0.depreciation_line_ids[1].amount, 500)
        vehicle0.compute_depreciation_board()
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

    def test_02_prorata_basic(self):
        """Prorata temporis depreciation basic test."""
        asset = self.asset_model.create({
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
        asset.compute_depreciation_board()
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

    def test_03_proprata_init_prev_year(self):
        """Prorata temporis depreciation with init value in prev year."""
        # I create an asset in current year
        asset = self.asset_model.create({
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

    def test_04_prorata_init_cur_year(self):
        """Prorata temporis depreciation with init value in curent year."""
        asset = self.asset_model.create({
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

    def test_05_degressive_linear(self):
        """Degressive-Linear with annual and quarterly depreciation."""

        # annual depreciation
        asset = self.asset_model.create({
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
        asset.compute_depreciation_board()
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
        asset = self.asset_model.create({
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
        asset.compute_depreciation_board()
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

    def test_06_degressive_limit(self):
        """Degressive with annual depreciation."""
        asset = self.asset_model.create({
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
        asset.compute_depreciation_board()
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

    def test_07_linear_limit(self):
        """Degressive with annual depreciation."""
        asset = self.asset_model.create({
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
        asset.compute_depreciation_board()
        asset.refresh()

        # check values in the depreciation board
        self.assertEquals(len(asset.depreciation_line_ids), 6)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               200.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount,
                               100.00, places=2)

    def test_08_asset_removal(self):
        """Asset removal"""
        asset = self.asset_model.create({
            'name': 'test asset removal',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 5000,
            'salvage_value': 0,
            'date_start': time.strftime('%Y-01-01'),
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'quarter',
            'prorata': False,
        })
        asset.compute_depreciation_board()
        asset.validate()
        wiz_ctx = {
            'active_id': asset.id,
            'early_removal': True,
        }
        wiz = self.remove_model.with_context(wiz_ctx).create({
            'date_remove': time.strftime('%Y-01-31'),
            'sale_value': 0.0,
            'posting_regime': 'gain_loss_on_sale',
            'account_plus_value_id': self.ref('account.a_sale'),
            'account_min_value_id': self.ref('account.a_expense'),
        })
        wiz.remove()
        asset.refresh()
        self.assertEquals(len(asset.depreciation_line_ids), 3)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount,
                               81.46, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount,
                               4918.54, places=2)

    def test_09_asset_from_invoice(self):
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

    def test_10_asset_from_invoice_product_item(self):
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
