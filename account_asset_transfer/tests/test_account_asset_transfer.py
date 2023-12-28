# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.account_asset_management.tests.test_account_asset_management import (
    TestAssetManagement,
)


@tagged("post_install", "-at_install")
class TestAccountAssetTransfer(TestAssetManagement):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Profile Under Construction
        cls.profile_auc = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "transfer_journal_id": cls.company_data["default_journal_misc"].id,
                "asset_product_item": True,
                "name": "Asset Under Construction",
                "method_time": "year",
                "method_number": 0,
                "method_period": "year",
            }
        )

        # Profile normal asset
        cls.profile_asset = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "asset_product_item": True,
                "name": "Room - 5 Years",
                "method_time": "year",
                "method_number": 5,
                "method_period": "year",
            }
        )

    def test_01_asset_transfer_auc_to_asset(self):
        """Create AUC and then transfer to normal asset class,
        I expect a new journal entry will be created"""
        # Create 3 AUC assets from an invoice
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(self.env.user)
        move_form.partner_id = self.partner
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "Wall"
            line_form.price_unit = 2000.00
            line_form.asset_profile_id = self.profile_auc
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "Roof"
            line_form.price_unit = 10000.00
            line_form.asset_profile_id = self.profile_auc
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "Floor"
            line_form.price_unit = 10000.00
            line_form.asset_profile_id = self.profile_auc
        self.invoice_auc = move_form.save()
        self.invoice_auc.invoice_line_ids.write(
            {"asset_profile_id": self.profile_auc.id}
        )
        self.invoice_auc.action_post()
        # Create AUC asset without move
        asset_auc = self.env["account.asset"].create(
            {
                "name": "Door",
                "profile_id": self.profile_auc.id,
                "purchase_value": 1000,
                "date_start": fields.Date.context_today(self.env.user),
            }
        )
        # Test can_transfer status
        assets = self.invoice_auc.invoice_line_ids.mapped("asset_id")
        assets += asset_auc
        self.assertFalse(list(set(assets.mapped("can_transfer")))[0])
        assets.validate()
        assets.invalidate_model()
        # can_transfer = True after validate
        self.assertTrue(list(set(assets.mapped("can_transfer")))[0])
        self.assertEqual(list(set(assets.mapped("is_transfer"))), [False])
        # Keep source asset
        source_assets = assets
        # Create Asset Transfer
        transfer_form = Form(
            self.env["account.asset.transfer"].with_context(active_ids=assets.ids)
        )
        transfer_wiz = transfer_form.save()
        with self.assertRaises(UserError):
            transfer_wiz.transfer()
        with transfer_form.to_asset_ids.new() as to_asset:
            to_asset.asset_name = "Asset 1"
            to_asset.asset_profile_id = self.profile_asset
            to_asset.quantity = 6
            to_asset.price_unit = 500
        with transfer_form.to_asset_ids.new() as to_asset:
            to_asset.asset_name = "Asset 2"
            to_asset.asset_profile_id = self.profile_asset
            to_asset.quantity = 1
            to_asset.price_unit = 20000
        transfer_form.save()
        # Test expand asset lines from quantity line
        self.assertEqual(len(transfer_wiz.to_asset_ids), 2)
        transfer_wiz.expand_to_asset_ids()
        self.assertEqual(len(transfer_wiz.to_asset_ids), 7)
        res = transfer_wiz.transfer()
        transfer_move = self.env["account.move"].browse(res["domain"][0][2])
        assets = transfer_move.invoice_line_ids.mapped("asset_id")
        # 2 new assets created, and value equal to original assets
        new_assets = assets.filtered(lambda l: l.state == "draft")
        self.assertEqual(sum(new_assets.mapped("purchase_value")), 23000)
        # All asset transfer will change to is_transfer
        self.assertEqual(list(set(assets.mapped("is_transfer"))), [True])
        # Check source asset from new asset
        result = new_assets[0].with_context(asset_from=1).open_assets()
        self.assertEqual(sorted(result["domain"][0][2]), source_assets.ids)
        # Check dest asset from source asset
        result = source_assets[0].with_context(asset_to=1).open_assets()
        self.assertEqual(result["domain"][0][2], new_assets.ids)
