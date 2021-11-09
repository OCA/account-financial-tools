# Copyright (c) 2014 ACSONE SA/NV (acsone.eu).
# Copyright 2009-2018 Noviat
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
import time
from datetime import date, datetime

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestAssetManagement(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # ENVIRONMENTS
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.dl_model = cls.env["account.asset.line"]
        cls.remove_model = cls.env["account.asset.remove"]
        # INSTANCES
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test", "standard_price": 500.0}
        )
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="in_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(cls.env.user)
        move_form.partner_id = cls.partner
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.product_id = cls.product
            line_form.price_unit = 2000.00
            line_form.quantity = 1
        cls.invoice = move_form.save()
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="in_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(cls.env.user)
        move_form.partner_id = cls.partner
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test 2"
            line_form.product_id = cls.product
            line_form.price_unit = 10000.00
            line_form.quantity = 1
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test 3"
            line_form.product_id = cls.product
            line_form.price_unit = 20000.00
            line_form.quantity = 1
        cls.invoice_2 = move_form.save()

        # analytic configuration
        cls.env.user.write(
            {
                "groups_id": [
                    (4, cls.env.ref("analytic.group_analytic_accounting").id),
                    (4, cls.env.ref("analytic.group_analytic_tags").id),
                ],
            }
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "test_analytic_account"}
        )
        cls.analytic_tag = cls.env["account.analytic.tag"].create(
            {"name": "test_analytic_tag"}
        )

        # Asset Profile 1
        cls.ict3Y = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Hardware - 3 Years",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        # Asset Profile 2
        cls.car5y = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Cars - 5 Years",
                "method_time": "year",
                "method_number": 5,
                "method_period": "year",
                "account_analytic_id": cls.analytic_account.id,
                "analytic_tag_ids": [(4, cls.analytic_tag.id)],
            }
        )

    def test_invoice_line_without_product(self):
        tax = self.env["account.tax"].create(
            {
                "name": "TAX 15%",
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "amount": 15.0,
            }
        )
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(self.env.user)
        move_form.partner_id = self.partner
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "Line 1"
            line_form.price_unit = 200.0
            line_form.quantity = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(tax)
        invoice = move_form.save()
        self.assertEqual(invoice.partner_id, self.partner)

    def test_00_fiscalyear_lock_date_month(self):
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1500,
                "date_start": "1901-02-01",
                "method_time": "year",
                "method_number": 3,
                "method_period": "month",
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        self.assertTrue(asset.depreciation_line_ids[0].init_entry)
        for i in range(1, 36):
            self.assertFalse(asset.depreciation_line_ids[i].init_entry)

    def test_00_fiscalyear_lock_date_year(self):
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1500,
                "date_start": "1901-02-01",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        self.assertTrue(asset.depreciation_line_ids[0].init_entry)
        for i in range(1, 4):
            self.assertFalse(asset.depreciation_line_ids[i].init_entry)

    def test_01_nonprorata_basic(self):
        """Basic tests of depreciation board computations and postings."""
        # First create demo assets and do some sanity checks
        # Asset Model 1
        ict0 = self.asset_model.create(
            {
                "state": "draft",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
                "name": "Laptop",
                "code": "PI00101",
                "purchase_value": 1500.0,
                "profile_id": self.ict3Y.id,
                "date_start": time.strftime("%Y-01-01"),
            }
        )
        # Sanity checks
        self.assertEqual(ict0.state, "draft")
        self.assertEqual(ict0.purchase_value, 1500)
        self.assertEqual(ict0.salvage_value, 0)
        self.assertEqual(ict0.depreciation_base, 1500)
        self.assertEqual(len(ict0.depreciation_line_ids), 1)
        # Asset Model 2
        vehicle0 = self.asset_model.create(
            {
                "state": "draft",
                "method_time": "year",
                "method_number": 5,
                "method_period": "year",
                "name": "CEO's Car",
                "purchase_value": 12000.0,
                "salvage_value": 2000.0,
                "profile_id": self.car5y.id,
                "date_start": time.strftime("%Y-01-01"),
            }
        )
        # Sanity checks
        self.assertEqual(vehicle0.state, "draft")
        self.assertEqual(vehicle0.purchase_value, 12000)
        self.assertEqual(vehicle0.salvage_value, 2000)
        self.assertEqual(vehicle0.depreciation_base, 10000)
        self.assertEqual(len(vehicle0.depreciation_line_ids), 1)
        # Compute the depreciation boards
        ict0.compute_depreciation_board()
        ict0.refresh()
        self.assertEqual(len(ict0.depreciation_line_ids), 4)
        self.assertEqual(ict0.depreciation_line_ids[1].amount, 500)
        vehicle0.compute_depreciation_board()
        vehicle0.refresh()
        self.assertEqual(len(vehicle0.depreciation_line_ids), 6)
        self.assertEqual(vehicle0.depreciation_line_ids[1].amount, 2000)
        # Post the first depreciation line
        ict0.validate()
        ict0.depreciation_line_ids[1].create_move()
        ict0.refresh()
        self.assertEqual(ict0.state, "open")
        self.assertEqual(ict0.value_depreciated, 500)
        self.assertEqual(ict0.value_residual, 1000)
        vehicle0.validate()
        created_move_ids = vehicle0.depreciation_line_ids[1].create_move()
        for move_id in created_move_ids:
            move = self.env["account.move"].browse(move_id)
            expense_line = move.line_ids.filtered(
                lambda line: line.account_id.internal_group == "expense"
            )
            self.assertEqual(
                expense_line.analytic_account_id.id,
                self.analytic_account.id,
            )
            self.assertEqual(expense_line.analytic_tag_ids.id, self.analytic_tag.id)
        vehicle0.refresh()
        self.assertEqual(vehicle0.state, "open")
        self.assertEqual(vehicle0.value_depreciated, 2000)
        self.assertEqual(vehicle0.value_residual, 8000)

    def test_02_prorata_basic(self):
        """Prorata temporis depreciation basic test."""
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 3333,
                "salvage_value": 0,
                "date_start": time.strftime("%Y-07-07"),
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
                "prorata": True,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[1].amount, 46.44, places=2
            )
        else:
            self.assertAlmostEqual(
                asset.depreciation_line_ids[1].amount, 47.33, places=2
            )
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount, 55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[4].amount, 55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[5].amount, 55.55, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[6].amount, 55.55, places=2)
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[-1].amount, 9.11, places=2
            )
        else:
            self.assertAlmostEqual(
                asset.depreciation_line_ids[-1].amount, 8.22, places=2
            )

    def test_03_proprata_init_prev_year(self):
        """Prorata temporis depreciation with init value in prev year."""
        # Create an asset in current year
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 3333,
                "salvage_value": 0,
                "date_start": "%d-07-07" % (datetime.now().year - 1,),
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
                "prorata": True,
            }
        )
        # Create a initial depreciation line in previous year
        self.dl_model.create(
            {
                "asset_id": asset.id,
                "amount": 325.08,
                "line_date": "%d-12-31" % (datetime.now().year - 1,),
                "type": "depreciate",
                "init_entry": True,
            }
        )
        self.assertEqual(len(asset.depreciation_line_ids), 2)
        asset.compute_depreciation_board()
        asset.refresh()
        # check the depreciated value is the initial value
        self.assertAlmostEqual(asset.value_depreciated, 325.08, places=2)
        # check computed values in the depreciation board
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 55.55, places=2)
        if calendar.isleap(date.today().year - 1):
            # for leap years the first year depreciation amount of 325.08
            # is too high and hence a correction is applied to the next
            # entry of the table
            self.assertAlmostEqual(
                asset.depreciation_line_ids[2].amount, 54.66, places=2
            )
            self.assertAlmostEqual(
                asset.depreciation_line_ids[3].amount, 55.55, places=2
            )
            self.assertAlmostEqual(
                asset.depreciation_line_ids[-1].amount, 9.11, places=2
            )
        else:
            self.assertAlmostEqual(
                asset.depreciation_line_ids[2].amount, 55.55, places=2
            )
            self.assertAlmostEqual(
                asset.depreciation_line_ids[-1].amount, 8.22, places=2
            )

    def test_04_prorata_init_cur_year(self):
        """Prorata temporis depreciation with init value in curent year."""
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 3333,
                "salvage_value": 0,
                "date_start": time.strftime("%Y-07-07"),
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
                "prorata": True,
            }
        )
        self.dl_model.create(
            {
                "asset_id": asset.id,
                "amount": 279.44,
                "line_date": time.strftime("%Y-11-30"),
                "type": "depreciate",
                "init_entry": True,
            }
        )
        self.assertEqual(len(asset.depreciation_line_ids), 2)
        asset.compute_depreciation_board()
        asset.refresh()
        # check the depreciated value is the initial value
        self.assertAlmostEqual(asset.value_depreciated, 279.44, places=2)
        # check computed values in the depreciation board
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[2].amount, 44.75, places=2
            )
        else:
            self.assertAlmostEqual(
                asset.depreciation_line_ids[2].amount, 45.64, places=2
            )
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 55.55, places=2)
        if calendar.isleap(date.today().year):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[-1].amount, 9.11, places=2
            )
        else:
            self.assertAlmostEqual(
                asset.depreciation_line_ids[-1].amount, 8.22, places=2
            )

    def test_05_degressive_linear(self):
        """Degressive-Linear with annual and quarterly depreciation."""
        # annual depreciation
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1000,
                "salvage_value": 0,
                "date_start": time.strftime("%Y-07-07"),
                "method_time": "year",
                "method": "degr-linear",
                "method_progress_factor": 0.40,
                "method_number": 5,
                "method_period": "year",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        # check values in the depreciation board
        self.assertEqual(len(asset.depreciation_line_ids), 5)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount, 400.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount, 240.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 200.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[4].amount, 160.00, places=2)
        # quarterly depreciation
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1000,
                "salvage_value": 0,
                "date_start": time.strftime("%Y-07-07"),
                "method_time": "year",
                "method": "degr-linear",
                "method_progress_factor": 0.40,
                "method_number": 5,
                "method_period": "quarter",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        # check values in the depreciation board
        self.assertEqual(len(asset.depreciation_line_ids), 15)
        # lines prior to asset start period are grouped in the first entry
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount, 300.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 60.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[7].amount, 50.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[13].amount, 40.00, places=2)

    def test_06_degressive_limit(self):
        """Degressive with annual depreciation."""
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1000,
                "salvage_value": 100,
                "date_start": time.strftime("%Y-07-07"),
                "method_time": "year",
                "method": "degr-limit",
                "method_progress_factor": 0.40,
                "method_number": 5,
                "method_period": "year",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        # check values in the depreciation board
        self.assertEqual(len(asset.depreciation_line_ids), 6)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount, 400.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount, 240.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[3].amount, 144.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[4].amount, 86.40, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[5].amount, 29.60, places=2)

    def test_07_linear_limit(self):
        """Degressive with annual depreciation."""
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1000,
                "salvage_value": 100,
                "date_start": time.strftime("%Y-07-07"),
                "method_time": "year",
                "method": "linear-limit",
                "method_number": 5,
                "method_period": "year",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        # check values in the depreciation board
        self.assertEqual(len(asset.depreciation_line_ids), 6)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount, 200.00, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount, 100.00, places=2)

    def test_08_asset_removal(self):
        """Asset removal"""
        asset = self.asset_model.create(
            {
                "name": "test asset removal",
                "profile_id": self.car5y.id,
                "purchase_value": 5000,
                "salvage_value": 0,
                "date_start": "2019-01-01",
                "method_time": "year",
                "method_number": 5,
                "method_period": "quarter",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.validate()
        wiz_ctx = {"active_id": asset.id, "early_removal": True}
        wiz = self.remove_model.with_context(wiz_ctx).create(
            {
                "date_remove": "2019-01-31",
                "sale_value": 0.0,
                "posting_regime": "gain_loss_on_sale",
                "account_plus_value_id": self.company_data[
                    "default_account_revenue"
                ].id,
                "account_min_value_id": self.company_data["default_account_expense"].id,
            }
        )
        wiz.remove()
        asset.refresh()
        self.assertEqual(len(asset.depreciation_line_ids), 3)
        self.assertAlmostEqual(asset.depreciation_line_ids[1].amount, 83.33, places=2)
        self.assertAlmostEqual(asset.depreciation_line_ids[2].amount, 4916.67, places=2)

    def test_09_asset_from_invoice(self):
        all_asset = self.env["account.asset"].search([])
        invoice = self.invoice
        asset_profile = self.car5y
        asset_profile.asset_product_item = False
        self.assertTrue(len(invoice.invoice_line_ids) > 0)
        line = invoice.invoice_line_ids[0]
        self.assertTrue(line.price_unit > 0.0)
        move_form = Form(invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.quantity = 2
            line_form.asset_profile_id = asset_profile
        invoice = move_form.save()
        invoice.action_post()
        # get all asset after invoice validation
        current_asset = self.env["account.asset"].search([])
        # get the new asset
        new_asset = current_asset - all_asset
        # check that a new asset is created
        self.assertEqual(len(new_asset), 1)
        # check that the new asset has the correct purchase value
        self.assertAlmostEqual(
            new_asset.purchase_value, line.price_unit * line.quantity, places=2
        )

    def test_10_asset_from_invoice_product_item(self):
        all_asset = self.env["account.asset"].search([])
        invoice = self.invoice
        asset_profile = self.car5y
        asset_profile.asset_product_item = True
        self.assertTrue(len(invoice.invoice_line_ids) > 0)
        line = invoice.invoice_line_ids[0]
        self.assertTrue(line.price_unit > 0.0)
        line.quantity = 2
        line.asset_profile_id = asset_profile
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        invoice.action_post()
        # get all asset after invoice validation
        current_asset = self.env["account.asset"].search([])
        # get the new asset
        new_asset = current_asset - all_asset
        # check that a new asset is created
        self.assertEqual(len(new_asset), 2)
        for asset in new_asset:
            # check that the new asset has the correct purchase value
            self.assertAlmostEqual(asset.purchase_value, line.price_unit, places=2)

    def test_11_assets_from_invoice(self):
        all_assets = self.env["account.asset"].search([])
        ctx = dict(self.invoice_2._context)
        del ctx["default_move_type"]
        invoice = self.invoice_2.with_context(ctx)
        asset_profile = self.car5y
        asset_profile.asset_product_item = True
        # Compute depreciation lines on invoice validation
        asset_profile.open_asset = True
        self.assertTrue(len(invoice.invoice_line_ids) == 2)
        invoice.invoice_line_ids.write(
            {"quantity": 1, "asset_profile_id": asset_profile.id}
        )
        invoice.action_post()
        # Retrieve all assets after invoice validation
        current_assets = self.env["account.asset"].search([])
        # What are the new assets?
        new_assets = current_assets - all_assets
        self.assertEqual(len(new_assets), 2)
        for asset in new_assets:
            dlines = asset.depreciation_line_ids.filtered(
                lambda l: l.type == "depreciate"
            )
            dlines = dlines.sorted(key=lambda l: l.line_date)
            self.assertAlmostEqual(dlines[0].depreciated_value, 0.0)
            self.assertAlmostEqual(dlines[-1].remaining_value, 0.0)

    def test_12_prorata_days_calc(self):
        """Prorata temporis depreciation with days calc option."""
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 3333,
                "salvage_value": 0,
                "date_start": "2019-07-07",
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
                "prorata": True,
                "days_calc": True,
                "use_leap_years": False,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        day_rate = 3333 / 1827  # 3333 / 1827 depreciation days
        for i in range(1, 10):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[i].amount,
                asset.depreciation_line_ids[i].line_days * day_rate,
                places=2,
            )
        # Last depreciation remaining
        self.assertAlmostEqual(asset.depreciation_line_ids[-1].amount, 11.05, places=2)

    def test_13_use_leap_year(self):
        # When you use the depreciation with years method and using lap years,
        # the depreciation amount is calculated as 10000 / 1826 days * 365 days
        # = yearly depreciation amount of 1998.90.
        # Then 1998.90 / 12 = 166.58
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 10000,
                "salvage_value": 0,
                "date_start": time.strftime("2019-01-01"),
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
                "prorata": False,
                "days_calc": False,
                "use_leap_years": True,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        for i in range(2, 11):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[i].amount, 166.58, places=2
            )
        self.assertAlmostEqual(
            asset.depreciation_line_ids[13].depreciated_value, 1998.90, places=2
        )

    def test_14_not_use_leap_year(self):
        # When you run a depreciation with method = 'year' and no not use
        # lap years you divide 1000 / 5 years = 2000, then divided by 12 months
        # to get 166.67 per month, equal for all periods.
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 10000,
                "salvage_value": 0,
                "date_start": time.strftime("2019-01-01"),
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
                "prorata": False,
                "days_calc": False,
                "use_leap_years": False,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        for _i in range(1, 11):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[1].amount, 166.67, places=2
            )
        # In the last month of the fiscal year we compensate for the small
        # deviations if that is necessary.
        self.assertAlmostEqual(asset.depreciation_line_ids[12].amount, 166.63, places=2)

    def test_15_account_asset_group(self):
        """Group's name_get behaves differently depending on code and context"""
        group_fa = self.env["account.asset.group"].create(
            {
                "name": "Fixed Assets",
                "code": "FA",
            }
        )
        group_tfa = self.env["account.asset.group"].create(
            {
                "name": "Tangible Fixed Assets",
                "code": "TFA",
            }
        )
        # Groups are displayed by code (if any) plus name
        self.assertEqual(
            self.env["account.asset.group"].name_search("FA"),
            [(group_fa.id, "FA Fixed Assets")],
        )
        # Groups with code are shown by code in list views
        self.assertEqual(
            self.env["account.asset.group"]
            .with_context(params={"view_type": "list"})
            .name_search("FA"),
            [(group_fa.id, "FA")],
        )
        self.assertEqual(
            self.env["account.asset.group"].name_search("TFA"),
            [(group_tfa.id, "TFA Tangible Fixed Assets")],
        )
        group_tfa.code = False
        group_fa.code = False
        self.assertEqual(group_fa.name_get(), [(group_fa.id, "Fixed Assets")])
        # Groups without code are shown by truncated name in lists
        self.assertEqual(
            group_tfa.name_get(), [(group_tfa.id, "Tangible Fixed Assets")]
        )
        self.assertEqual(
            group_tfa.with_context(params={"view_type": "list"}).name_get(),
            [(group_tfa.id, "Tangible Fixed A...")],
        )
        self.assertFalse(self.env["account.asset.group"].name_search("stessA dexiF"))

    def test_16_use_number_of_depreciations(self):
        # When you run a depreciation with method = 'number'
        profile = self.car5y
        profile.method_time = "number"
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": profile.id,
                "purchase_value": 10000,
                "salvage_value": 0,
                "date_start": time.strftime("2019-01-01"),
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
                "prorata": False,
                "days_calc": False,
                "use_leap_years": False,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        for _i in range(1, 11):
            self.assertAlmostEqual(
                asset.depreciation_line_ids[1].amount, 166.67, places=2
            )
        # In the last month of the fiscal year we compensate for the small
        # deviations if that is necessary.
        self.assertAlmostEqual(asset.depreciation_line_ids[12].amount, 166.63, places=2)

    def test_20_asset_removal_with_value_residual(self):
        """Asset removal with value residual"""
        asset = self.asset_model.create(
            {
                "name": "test asset removal",
                "profile_id": self.car5y.id,
                "purchase_value": 1000,
                "salvage_value": 0,
                "date_start": "2019-01-01",
                "method_time": "number",
                "method_number": 10,
                "method_period": "month",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.validate()
        lines = asset.depreciation_line_ids.filtered(lambda x: not x.init_entry)
        self.assertEqual(len(lines), 10)
        last_line = lines[-1]
        last_line["amount"] = last_line["amount"] - 0.10
        for asset_line in lines:
            asset_line.create_move()
        self.assertEqual(asset.value_residual, 0.10)
        asset.compute_depreciation_board()
        lines = asset.depreciation_line_ids.filtered(lambda x: not x.init_entry)
        self.assertEqual(len(lines), 11)
        last_line = lines[-1]
        self.assertEqual(last_line.amount, 0.10)
        last_line.create_move()
        self.assertEqual(asset.value_residual, 0)
        self.assertEqual(asset.state, "close")
