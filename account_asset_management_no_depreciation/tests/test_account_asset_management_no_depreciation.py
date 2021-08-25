# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestAssetManagementNoDepreciation(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.remove_model = cls.env["account.asset.remove"]

        # Asset Profile
        cls.asset_profile = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Asset Non-Depreciation",
                "no_depreciation": True,
                "method_time": "year",
                "method_number": 0,
                "method_period": "year",
            }
        )

    def test_01_asset_no_depreciation(self):
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.asset_profile.id,
                "purchase_value": 1500,
                "date_start": "2021-01-01",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
                "no_depreciation": False,
            }
        )
        asset._compute_no_depreciation()
        self.assertEqual(asset.state, "draft")
        self.assertTrue(asset.no_depreciation)
        # Compute Depreciation and Confirm Asset
        asset.compute_depreciation_board()
        asset.validate()
        self.assertEqual(asset.state, "open")
        self.assertEqual(len(asset.depreciation_line_ids), 1)
        self.assertTrue(asset.depreciation_line_ids[0].init_entry)
        # Remove Asset
        asset.remove()
        asset.refresh()
        self.assertEqual(asset.state, "removed")
        self.assertEqual(len(asset.depreciation_line_ids), 1)
