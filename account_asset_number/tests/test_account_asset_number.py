# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo.tests import tagged

from odoo.addons.account_asset_management.tests.test_account_asset_management import (
    TestAssetManagement,
)


@tagged("post_install", "-at_install")
class TestAssetNumber(TestAssetManagement):
    @classmethod
    def setUpClass(cls):
        """Setup."""
        super().setUpClass()
        cls.sequence_asset = cls.env["ir.sequence"].create(
            {
                "name": "Asset Number Test",
                "code": "account.asset.sequence",
                "implementation": "standard",
                "prefix": "AC",
                "padding": 5,
            }
        )

    def test_01_asset_number(self):
        """Test asset creation with a sequence."""

        self.car5y.write(
            {
                "use_sequence": True,
                "sequence_id": self.sequence_asset.id,
            }
        )
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
        asset.invalidate_recordset()
        # check number in the asset
        self.assertFalse(asset.number)
        asset.validate()
        self.assertTrue(asset.number)
        self.assertEqual(asset.number[:2], "AC")

    def test_02_asset_number_without_sequence(self):
        """Test asset creation without a sequence."""
        self.car5y.write(
            {
                "use_sequence": False,
                "sequence_id": self.sequence_asset.id,
            }
        )

        asset = self.asset_model.create(
            {
                "name": "test asset without sequence",
                "profile_id": self.car5y.id,
                "purchase_value": 1500,
                "salvage_value": 100,
                "date_start": time.strftime("%Y-08-01"),
                "method_time": "year",
                "method": "degr-linear",
                "method_number": 5,
                "method_period": "year",
                "prorata": False,
            }
        )

        asset.validate()

        self.assertFalse(
            asset.number,
            "The asset number should not be generated when sequence is disabled.",
        )

    def test_03_xls_fields(self):
        """Test XLS fields include the number field."""
        acquisition_fields = self.env["account.asset"]._xls_acquisition_fields()
        active_fields = self.env["account.asset"]._xls_active_fields()
        removal_fields = self.env["account.asset"]._xls_removal_fields()

        self.assertIn(
            "number",
            acquisition_fields,
            "The number field should be included in acquisition fields.",
        )
        self.assertIn(
            "number",
            active_fields,
            "The number field should be included in active fields.",
        )
        self.assertIn(
            "number",
            removal_fields,
            "The number field should be included in removal fields.",
        )

    def test_04_profile_barcode_type_onchange(self):
        """Test the onchange logic for barcode_type."""
        self.ict3Y.write(
            {
                "barcode_width": 350,
                "barcode_height": 75,
            }
        )

        self.ict3Y.barcode_type = "qr"
        self.ict3Y._onchange_barcode_type()
        self.assertEqual(
            self.ict3Y.barcode_width, 150, "QR barcode width should default to 150."
        )
        self.assertEqual(
            self.ict3Y.barcode_height,
            75,
            "Barcode height should remain unchanged for QR.",
        )

        self.ict3Y.barcode_type = "barcode"
        self.ict3Y._onchange_barcode_type()
        self.assertEqual(
            self.ict3Y.barcode_width, 300, "Barcode width should default to 300."
        )
        self.assertEqual(
            self.ict3Y.barcode_height, 75, "Barcode height should default to 75."
        )
