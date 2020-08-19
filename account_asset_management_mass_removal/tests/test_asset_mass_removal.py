# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, tools
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_resource_path
from odoo.tests.common import SavepointCase


class TestAssetMassRemoval(SavepointCase):
    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(
            cls.cr,
            module,
            get_resource_path(module, *args),
            {},
            "init",
            False,
            "test",
            cls.registry._assertion_report,
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._load("account", "test", "account_minimal_test.xml")
        cls._load("account_asset_management", "tests", "account_asset_test_data.xml")

    def _create_asset_removal_line(self, assets, date_remove, sale_value):
        return [
            (
                0,
                0,
                {
                    "asset_id": asset.id,
                    "date_remove": date_remove,
                    "sale_value": sale_value or 0.0,
                },
            )
            for asset in assets
        ]

    def _create_asset_removal(self, assets, date_remove, sale_value):
        asset_removal = self.env["account.asset.removal"].create(
            {
                "removal_asset_ids": assets
                and self._create_asset_removal_line(assets, date_remove, sale_value)
                or False
            }
        )
        return asset_removal

    def _update_profile_account_min_plus(
        self,
        assets,
        account_plus_value,
        account_min_value,
        account_residual_value=False,
    ):
        for asset in assets:
            asset.profile_id.write(
                {
                    "account_plus_value_id": account_plus_value,
                    "account_min_value_id": account_min_value,
                    "account_residual_value_id": account_residual_value,
                }
            )

    def test_01_remove_asset_flow(self):
        account_plus_value = self.browse_ref("account.a_sale")
        account_min_value = self.browse_ref("account.a_expense")
        ict0 = self.browse_ref("account_asset_management.account_asset_asset_ict0")
        vehicle0 = self.browse_ref(
            "account_asset_management.account_asset_asset_vehicle0"
        )
        assets = ict0 + vehicle0
        # Update profile_id in asset
        self._update_profile_account_min_plus(
            assets, account_plus_value, account_min_value
        )
        assets.validate()
        # Create 2 asset line in asset removal
        date_remove = fields.Date.today()
        with self.assertRaises(ValidationError):
            self._create_asset_removal(ict0, date_remove, -1)
        with self.assertRaises(UserError):
            self._create_asset_removal(False, date_remove, 0.0).remove()
        asset_removal = self._create_asset_removal(assets, date_remove, 0.0)
        self.assertFalse(asset_removal.removal_asset_ids.account_plus_value_id)
        self.assertFalse(asset_removal.removal_asset_ids.account_min_value_id)
        asset_removal.removal_asset_ids._onchange_account_value_id()
        self.assertTrue(asset_removal.removal_asset_ids.account_plus_value_id)
        self.assertTrue(asset_removal.removal_asset_ids.account_min_value_id)
        asset_removal.cancel()
        asset_removal.set_to_draft()
        asset_removal.remove()
        # Check state asset removal, state each asset
        self.assertEqual(asset_removal.source_asset_count, 2)
        self.assertEqual(asset_removal.state, "done")
        self.assertEqual(
            len(set(asset_removal.removal_asset_ids.mapped("asset_id.state"))), 1
        )
        for asset_state in asset_removal.removal_asset_ids.mapped("asset_id.state"):
            self.assertEqual(asset_state, "removed")
        asset_removal.open_asset_removed()
        asset_removal.open_entries()
