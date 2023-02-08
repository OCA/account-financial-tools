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
        # use sequence number on profile_id
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
        asset.refresh()
        # check number in the asset
        self.assertFalse(asset.number)
        asset.validate()
        self.assertTrue(asset.number)
        self.assertEqual(asset.number[:2], "AC")
