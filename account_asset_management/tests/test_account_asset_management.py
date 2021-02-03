# Copyright (c) 2014 ACSONE SA/NV (acsone.eu).
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
from datetime import date, datetime
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
        super().setUpClass()

        cls._load('account', 'test', 'account_minimal_test.xml')
        cls._load('account_asset_management', 'tests',
                  'account_asset_test_data.xml')

        # ENVIRONEMENTS
        cls.asset_model = cls.env['account.asset']
        cls.dl_model = cls.env['account.asset.line']
        cls.remove_model = cls.env['account.asset.remove']
        cls.account_invoice = cls.env['account.invoice']
        cls.account_move_line = cls.env['account.move.line']
        cls.account_account = cls.env['account.account']
        cls.account_journal = cls.env['account.journal']
        cls.account_invoice_line = cls.env['account.invoice.line']

        # INSTANCES

        # Instance: company
        cls.company = cls.env.ref('base.main_company')

        # Instance: account type (receivable)
        cls.type_recv = cls.env.ref('account.data_account_type_receivable')

        # Instance: account type (payable)
        cls.type_payable = cls.env.ref('account.data_account_type_payable')

        # Instance: account (receivable)
        cls.account_recv = cls.account_account.create({
            'name': 'test_account_receivable',
            'code': '123',
            'user_type_id': cls.type_recv.id,
            'company_id': cls.company.id,
            'reconcile': True})

        # Instance: account (payable)
        cls.account_payable = cls.account_account.create({
            'name': 'test_account_payable',
            'code': '321',
            'user_type_id': cls.type_payable.id,
            'company_id': cls.company.id,
            'reconcile': True})

        # Instance: partner
        cls.partner = cls.env.ref('base.res_partner_2')

        # Instance: journal
        cls.journal = cls.account_journal.search(
            [('type', '=', 'purchase')])[0]

        # Instance: product
        cls.product = cls.env.ref('product.product_product_4')

        # Instance: invoice line
        cls.invoice_line = cls.account_invoice_line.create({
            'name': 'test',
            'account_id': cls.account_payable.id,
            'price_unit': 2000.00,
            'quantity': 1,
            'product_id': cls.product.id})

        # Instance: invoice
        cls.invoice = cls.account_invoice.create({
            'partner_id': cls.partner.id,
            'account_id': cls.account_recv.id,
            'journal_id': cls.journal.id,
            'invoice_line_ids': [(4, cls.invoice_line.id)]})

        cls.invoice_line_2 = cls.account_invoice_line.create({
            'name': 'test 2',
            'account_id': cls.account_payable.id,
            'price_unit': 10000.00,
            'quantity': 1,
            'product_id': cls.product.id})
        cls.invoice_line_3 = cls.account_invoice_line.create({
            'name': 'test 3',
            'account_id': cls.account_payable.id,
            'price_unit': 20000.00,
            'quantity': 1,
            'product_id': cls.product.id})

        cls.invoice_2 = cls.account_invoice.create({
            'partner_id': cls.partner.id,
            'account_id': cls.account_recv.id,
            'journal_id': cls.journal.id,
            'invoice_line_ids': [(4, cls.invoice_line_2.id),
                                 (4, cls.invoice_line_3.id)]})

    def test_01_nonprorata_basic(self):
        """Basic tests of depreciation board computations and postings."""
        #
        # first load demo assets and do some sanity checks
        #
        ict0 = self.browse_ref('account_asset_management.'
                               'account_asset_asset_ict0')
        self.assertEqual(ict0.state, 'draft')
        self.assertEqual(ict0.purchase_value, 1500)
        self.assertEqual(ict0.salvage_value, 0)
        self.assertEqual(ict0.depreciation_base, 1500)
        self.assertEqual(len(ict0.depreciation_line_ids), 1)
        vehicle0 = self.browse_ref('account_asset_management.'
                                   'account_asset_asset_vehicle0')
        self.assertEqual(vehicle0.state, 'draft')
        self.assertEqual(vehicle0.purchase_value, 12000)
        self.assertEqual(vehicle0.salvage_value, 2000)
        self.assertEqual(vehicle0.depreciation_base, 10000)
        self.assertEqual(len(vehicle0.depreciation_line_ids), 1)

        #
        # I compute the depreciation boards
        #
        ict0.compute_depreciation_board()
        ict0.refresh()
        self.assertEqual(len(ict0.depreciation_line_ids), 4)
        self.assertEqual(ict0.depreciation_line_ids[1].amount, 500)
        vehicle0.compute_depreciation_board()
        vehicle0.refresh()
        self.assertEqual(len(vehicle0.depreciation_line_ids), 6)
        self.assertEqual(vehicle0.depreciation_line_ids[1].amount, 2000)

        #
        # I post the first depreciation line
        #
        ict0.validate()
        ict0.depreciation_line_ids[1].create_move()
        ict0.refresh()
        self.assertEqual(ict0.state, 'open')
        self.assertEqual(ict0.value_depreciated, 500)
        self.assertEqual(ict0.value_residual, 1000)
        vehicle0.validate()
        vehicle0.depreciation_line_ids[1].create_move()
        vehicle0.refresh()
        self.assertEqual(vehicle0.state, 'open')
        self.assertEqual(vehicle0.value_depreciated, 2000)
        self.assertEqual(vehicle0.value_residual, 8000)

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
        self.assertEqual(len(asset.depreciation_line_ids), 2)
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
        self.assertEqual(len(asset.depreciation_line_ids), 2)
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
        self.assertEqual(len(asset.depreciation_line_ids), 5)
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
        self.assertEqual(len(asset.depreciation_line_ids), 15)
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
        self.assertEqual(len(asset.depreciation_line_ids), 6)
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
        self.assertEqual(len(asset.depreciation_line_ids), 6)
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
            'date_start': '2019-01-01',
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
            'date_remove': '2019-01-31',
            'sale_value': 0.0,
            'posting_regime': 'gain_loss_on_sale',
            'account_plus_value_id': self.ref('account.a_sale'),
            'account_min_value_id': self.ref('account.a_expense'),
        })
        wiz.remove()
        asset.refresh()
        self.assertEqual(len(asset.depreciation_line_ids), 3)
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

    def test_11_assets_from_invoice(self):
        all_assets = self.env['account.asset'].search([])
        invoice = self.invoice_2
        asset_profile = self.env.ref(
            'account_asset_management.account_asset_profile_car_5Y')
        asset_profile.asset_product_item = True
        # Compute depreciation lines on invoice validation
        asset_profile.open_asset = True

        self.assertTrue(len(invoice.invoice_line_ids) == 2)
        invoice.invoice_line_ids.write({
            'quantity': 1,
            'asset_profile_id': asset_profile.id,
        })
        invoice.action_invoice_open()
        # Retrieve all assets after invoice validation
        current_assets = self.env['account.asset'].search([])
        # What are the new assets?
        new_assets = current_assets - all_assets
        self.assertEqual(len(new_assets), 2)

        for asset in new_assets:
            dlines = asset.depreciation_line_ids.filtered(
                lambda l: l.type == 'depreciate')
            dlines = dlines.sorted(key=lambda l: l.line_date)
            self.assertAlmostEqual(dlines[0].depreciated_value, 0.0)
            self.assertAlmostEqual(dlines[-1].remaining_value, 0.0)

    def test_12_prorata_days_calc(self):
        """Prorata temporis depreciation with days calc option."""
        asset = self.asset_model.create({
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 3333,
            'salvage_value': 0,
            'date_start': '2019-07-07',
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'month',
            'prorata': True,
            'days_calc': True,
            'use_leap_years': False,
        })
        asset.compute_depreciation_board()
        asset.refresh()
        day_rate = 3333 / 1827  # 3333 / 1827 depreciation days
        for i in range(1, 10):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[i].amount,
                asset.depreciation_line_ids[i].line_days * day_rate, places=2)
        # Last depreciation remaining
        self.assertAlmostEqual(
            asset.depreciation_line_ids[-1].amount, 11.05, places=2)

    def test_13_use_leap_year(self):
        # When you use the depreciation with years method and using lap years,
        # the depreciation amount is calculated as 10000 / 1826 days * 365 days
        # = yearly depreciation amount of 1998.90.
        # Then 1998.90 / 12 = 166.58
        asset = self.asset_model.create({
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 10000,
            'salvage_value': 0,
            'date_start': time.strftime('2019-01-01'),
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'month',
            'prorata': False,
            'days_calc': False,
            'use_leap_years': True,
        })
        asset.compute_depreciation_board()
        asset.refresh()
        for i in range(2, 11):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[i].amount, 166.58, places=2)
        self.assertAlmostEqual(
            asset.depreciation_line_ids[13].depreciated_value, 1998.90,
            places=2)

    def test_14_not_use_leap_year(self):
        # When you run a depreciation with method = 'year' and no not use
        # lap years you divide 1000 / 5 years = 2000, then divided by 12 months
        # to get 166.67 per month, equal for all periods.
        asset = self.asset_model.create({
            'name': 'test asset',
            'profile_id': self.ref('account_asset_management.'
                                   'account_asset_profile_car_5Y'),
            'purchase_value': 10000,
            'salvage_value': 0,
            'date_start': time.strftime('2019-01-01'),
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'month',
            'prorata': False,
            'days_calc': False,
            'use_leap_years': False,
        })
        asset.compute_depreciation_board()
        asset.refresh()
        for i in range(1, 11):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[1].amount, 166.67, places=2)
        # In the last month of the fiscal year we compensate for the small
        # deviations if that is necessary.
        self.assertAlmostEqual(
            asset.depreciation_line_ids[12].amount, 166.63, places=2)

    def test_15_account_asset_group(self):
        """ Group's name_get behaves differently depending on code and context
        """
        group_fa = self.env.ref(
            'account_asset_management.account_asset_group_fa')
        group_tfa = self.env.ref(
            'account_asset_management.account_asset_group_tfa')
        # Groups are displayed by code (if any) plus name
        self.assertEqual(
            self.env['account.asset.group']._name_search('FA'),
            [(group_fa.id, 'FA Fixed Assets')])
        # Groups with code are shown by code in list views
        self.assertEqual(
            self.env['account.asset.group'].with_context(
                params={'view_type': 'list'})._name_search('FA'),
            [(group_fa.id, 'FA')])
        self.assertEqual(
            self.env['account.asset.group']._name_search('TFA'),
            [(group_tfa.id, 'TFA Tangible Fixed Assets')])
        group_tfa.code = False
        group_fa.code = False
        self.assertEqual(
            group_fa.name_get(),
            [(group_fa.id, 'Fixed Assets')])
        # Groups without code are shown by truncated name in lists
        self.assertEqual(
            group_tfa.name_get(),
            [(group_tfa.id, 'Tangible Fixed Assets')])
        self.assertEqual(
            group_tfa.with_context(params={'view_type': 'list'}).name_get(),
            [(group_tfa.id, 'Tangible Fixed A...')])
        self.assertFalse(
            self.env['account.asset.group']._name_search('stessA dexiF'))
