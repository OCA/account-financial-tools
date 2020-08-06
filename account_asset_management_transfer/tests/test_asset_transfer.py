# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import tools
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tests.common import SavepointCase


class TestAssetTransfer(SavepointCase):
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
        cls.config = cls.env["res.config.settings"]
        cls.journal = cls.env["account.journal"]
        cls.move = cls.env["account.move"]
        cls.journal_id = cls.journal.search([("type", "=", "general")], limit=1)
        cls.partner_id = cls.env.ref("base.res_partner_2")
        # Enable config asset transfer
        cls.config.create(
            {
                "asset_transfer_settings": True,
                "asset_transfer_journal_id": cls.journal_id,
            }
        ).execute()

    def _create_asset_from_invoice(self, price_unit, multi=False):
        if not multi:
            multi = 1
        invoice = self.move.create(
            {
                "partner_id": self.partner_id,
                "type": "in_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Asset #%s" % (x + 1),
                            "asset_profile_id": self.ref(
                                "account_asset_management.account_asset_profile_car_5Y"
                            ),
                            "price_unit": 100.0,
                        },
                    )
                    for x in range(multi)
                ],
            }
        )
        invoice.action_post()
        return invoice

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

    def _create_asset_transfer(self, assets, date_transfer=False, multi_target=False):
        if not multi_target:
            multi_target = 1
        source_asset_value = sum(assets.mapped("purchase_value"))
        asset_transfer = self.env["account.asset.transfer"].create(
            {
                "date_transfer": date_transfer,
                "source_asset_ids": assets.ids,
                "target_asset_ids": [
                    (
                        0,
                        0,
                        {
                            "asset_profile_id": self.ref(
                                "account_asset_management.account_asset_profile_car_5Y"
                            ),
                            "asset_name": "Target New Asset #%s" % (x + 1),
                            "depreciation_base": source_asset_value / multi_target,
                        },
                    )
                    for x in range(multi_target)
                ],
            }
        )
        return asset_transfer

    def test_01_transfer_asset_direct(self):
        ict0 = self.browse_ref("account_asset_management.account_asset_asset_ict0")
        account_plus_value = self.browse_ref("account.a_sale")
        account_min_value = self.browse_ref("account.a_expense")
        ict0.validate()
        self.assertEqual(ict0.state, "open")
        date_transfer = ict0.date_start + relativedelta(days=10)
        asset_transfer = self._create_asset_transfer(ict0, date_transfer, 2)
        self.assertEqual(len(asset_transfer.source_asset_ids), 1)
        asset_transfer.cancel()
        asset_transfer.set_to_draft()
        # source and target not equal
        with self.assertRaises(ValidationError):
            asset_transfer.transfer()
        self.assertEqual(len(asset_transfer.target_asset_ids), 2)
        # don't config min and plus account in profile_id
        with self.assertRaises(ValidationError):
            asset_transfer.transfer()
        self._update_profile_account_min_plus(
            ict0, account_plus_value, account_min_value
        )
        with self.assertRaises(ValidationError):
            asset_transfer.transfer()

    def test_02_transfer_asset_one_many(self):
        account_plus_value = self.browse_ref("account.a_sale")
        account_min_value = self.browse_ref("account.a_expense")
        # Create 1 asset from invoice
        self._create_asset_from_invoice(100)
        asset = self.env["account.asset"].search(
            [("account_move_line_ids", "!=", False)]
        )
        asset.validate()
        date_transfer = asset.date_start + relativedelta(days=10)
        # source 1 target 2
        asset_transfer = self._create_asset_transfer(asset, date_transfer, 2)
        self._update_profile_account_min_plus(
            asset, account_plus_value, account_min_value
        )
        asset_transfer.transfer()

    def test_03_transfer_asset_many_one(self):
        account_plus_value = self.browse_ref("account.a_sale")
        account_min_value = self.browse_ref("account.a_expense")
        # Create 2 asset from invoice
        self._create_asset_from_invoice(100, 2)
        assets = self.env["account.asset"].search(
            [("account_move_line_ids", "!=", False)]
        )
        assets.validate()
        date_transfer = assets[0].date_start + relativedelta(days=10)
        # source 2 target 1
        asset_transfer = self._create_asset_transfer(assets, date_transfer)
        self._update_profile_account_min_plus(
            assets, account_plus_value, account_min_value
        )
        asset_transfer.transfer()

    def test_04_transfer_asset_depreciation(self):
        account_plus_value = self.browse_ref("account.a_sale")
        account_min_value = self.browse_ref("account.a_expense")
        # Create 1 asset from invoice
        self._create_asset_from_invoice(100)
        asset = self.env["account.asset"].search(
            [("account_move_line_ids", "!=", False)]
        )
        asset.validate()
        # Run depreciation 1 time
        asset.depreciation_line_ids[1].create_move()
        asset.refresh()
        old_value_depreciated = asset.value_depreciated
        date_transfer = asset.depreciation_line_ids[1].line_date + relativedelta(
            days=10
        )
        # source 1 target 2
        asset_transfer = self._create_asset_transfer(asset, date_transfer, 2)
        self._update_profile_account_min_plus(
            asset, account_plus_value, account_min_value
        )
        asset_transfer.transfer()
        # check value new asset
        for new_asset in asset_transfer.new_asset_ids:
            self.assertEqual(new_asset.date_start, date_transfer)
            self.assertEqual(
                new_asset.purchase_value,
                (asset.purchase_value - old_value_depreciated) / 2,
            )
        # open source asset
        result = asset_transfer.open_source_asset()
        ids = result.get("domain", False)[0][2]
        self.assertEqual(asset_transfer.source_asset_ids.ids, ids)
        # open target asset
        result = asset_transfer.open_target_asset()
        ids = result.get("domain", False)[0][2]
        self.assertEqual(asset_transfer.new_asset_ids.ids, ids)
        # open journal
        result = asset_transfer.open_entries()
        move_model = result.get("res_model", False)
        self.assertEqual(move_model, "account.move")
