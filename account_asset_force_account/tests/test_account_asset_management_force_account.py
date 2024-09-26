# Copyright 2024 Bernat Obrador(APSL-Nagarro)<bobrador@apsl.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAssetManagement(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]

        cls.account_depreciation_car = cls.env["account.account"].create(
            {
                "name": "Fixed Asset - Vehicle",
                "code": "151001",
                "account_type": "asset_fixed",
            }
        )

        cls.account_expense_laptop = cls.env["account.account"].create(
            {
                "name": "Depreciation Expense Account - Laptop",
                "code": "600001",
                "account_type": "expense",
            }
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
            }
        )

    def test_change_asset_accounts(self):
        ict0 = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.ict3Y.id,
                "purchase_value": 1500,
                "date_start": "1901-02-01",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
                "account_depreciation_id": self.ict3Y.account_depreciation_id.id,
                "account_expense_depreciation_id": self.account_expense_laptop.id,
            }
        )

        self.assertEqual(ict0.state, "draft")
        self.assertEqual(ict0.purchase_value, 1500)
        self.assertEqual(ict0.salvage_value, 0)
        self.assertEqual(ict0.depreciation_base, 1500)
        self.assertEqual(len(ict0.depreciation_line_ids), 1)
        self.assertEqual(ict0.account_asset_id.id, ict0.profile_id.account_asset_id.id)
        self.assertEqual(
            ict0.account_depreciation_id.id, ict0.profile_id.account_depreciation_id.id
        )
        self.assertEqual(
            ict0.account_expense_depreciation_id.id, self.account_expense_laptop.id
        )

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
                "account_depreciation_id": self.account_depreciation_car.id,
                "account_expense_depreciation_id": self.car5y.account_expense_depreciation_id.id,
            }
        )
        self.assertEqual(vehicle0.state, "draft")
        self.assertEqual(vehicle0.purchase_value, 12000)
        self.assertEqual(vehicle0.salvage_value, 2000)
        self.assertEqual(vehicle0.depreciation_base, 10000)
        self.assertEqual(len(vehicle0.depreciation_line_ids), 1)
        self.assertEqual(
            vehicle0.account_asset_id.id, vehicle0.profile_id.account_asset_id.id
        )
        self.assertEqual(
            vehicle0.account_depreciation_id.id, self.account_depreciation_car.id
        )
        self.assertEqual(
            vehicle0.account_expense_depreciation_id.id,
            vehicle0.profile_id.account_expense_depreciation_id.id,
        )

        ict0.compute_depreciation_board()
        ict0.invalidate_recordset()
        self.assertEqual(len(ict0.depreciation_line_ids), 4)
        self.assertEqual(ict0.depreciation_line_ids[1].amount, 500)

        vehicle0.compute_depreciation_board()
        vehicle0.invalidate_recordset()
        self.assertEqual(len(vehicle0.depreciation_line_ids), 6)
        self.assertEqual(vehicle0.depreciation_line_ids[1].amount, 2000)

        ict0.validate()
        ict0_created_moves_ids = ict0.depreciation_line_ids[1].create_move()
        ict0.invalidate_recordset()

        for move_id in ict0_created_moves_ids:
            move = self.env["account.move"].browse(move_id)

            # Validate that the profile account is used
            depr_line = move.line_ids.filtered(
                lambda line: line.account_id == self.ict3Y.account_depreciation_id
            )
            self.assertTrue(depr_line)

            # Validate that the forced expense depreciation account is being used
            expense_line = move.line_ids.filtered(
                lambda line: line.account_id == self.account_expense_laptop
            )
            self.assertTrue(expense_line)

        # Check that the asset is now open and depreciation is posted correctly
        self.assertEqual(ict0.state, "open")
        self.assertEqual(ict0.value_depreciated, 500)
        self.assertEqual(ict0.value_residual, 1000)

        vehicle0.validate()
        vehicle0_created_move_ids = vehicle0.depreciation_line_ids[1].create_move()
        for move_id in vehicle0_created_move_ids:
            move = self.env["account.move"].browse(move_id)

            # Validate that the forced depreciation account is being used
            depr_line = move.line_ids.filtered(
                lambda line: line.account_id == self.account_depreciation_car
            )
            self.assertTrue(depr_line)

            # Validate that the profile account is used
            expense_line = move.line_ids.filtered(
                lambda line: line.account_id
                == self.car5y.account_expense_depreciation_id
            )
            self.assertTrue(expense_line)

        vehicle0.invalidate_recordset()

        # Ensure the asset's state and values are correct after depreciation posting
        self.assertEqual(vehicle0.state, "open")
        self.assertEqual(vehicle0.value_depreciated, 2000)
        self.assertEqual(vehicle0.value_residual, 8000)

        vehicle0.invalidate_recordset()
