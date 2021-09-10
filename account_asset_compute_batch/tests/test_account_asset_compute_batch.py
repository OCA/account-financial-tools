# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from freezegun import freeze_time

from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.account_asset_management.tests.test_account_asset_management import (
    TestAssetManagement,
)


@tagged("post_install", "-at_install")
class TestAssetComputeBatch(TestAssetManagement):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create 3 assets from 2 profiles
        cls.ict0 = cls.asset_model.create(
            {
                "state": "draft",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
                "name": "Laptop",
                "code": "PI00101",
                "purchase_value": 1500.0,
                "profile_id": cls.ict3Y.id,
                "date_start": time.strftime("2000-01-01"),
            }
        )
        cls.ict1 = cls.asset_model.create(
            {
                "state": "draft",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
                "name": "Monitor",
                "code": "PI00102",
                "purchase_value": 2100.0,
                "profile_id": cls.ict3Y.id,
                "date_start": time.strftime("2000-01-01"),
            }
        )
        # 2nd asset
        cls.vehicle0 = cls.asset_model.create(
            {
                "state": "draft",
                "method_time": "year",
                "method_number": 5,
                "method_period": "year",
                "name": "CEO's Car",
                "purchase_value": 12000.0,
                "salvage_value": 2000.0,
                "profile_id": cls.car5y.id,
                "date_start": time.strftime("2000-01-01"),
            }
        )

    def _create_compute_wizard(self, use_batch=False, delay_compute=False):
        with Form(self.env["account.asset.compute"]) as f:
            f.batch_name = "Test Batch"
            f.description = "Compute asset with 2 profiles"
            f.profile_ids.add(self.ict3Y)
            f.profile_ids.add(self.car5y)
            f.use_batch = use_batch
            f.delay_compute = delay_compute
        wiz = f.save()
        return wiz

    @freeze_time("2000-12-31")
    def test_01_asset_compute_batch_normal(self):
        # Confirm 3 assets
        self.ict0.validate()
        self.assertEqual(self.ict0.depreciation_line_ids[1].amount, 500)
        self.ict1.validate()
        self.assertEqual(self.ict1.depreciation_line_ids[1].amount, 700)
        self.vehicle0.validate()
        self.assertEqual(self.vehicle0.depreciation_line_ids[1].amount, 2000)
        # Compute Asset, no delay
        wiz = self._create_compute_wizard(use_batch=True)
        res = wiz.asset_compute()
        batch = self.env["account.asset.compute.batch"].browse(res["res_id"])
        self.assertEqual(batch.state, "computed")
        self.assertEqual(batch.depre_amount, 3200)
        # Test summary amount by profile
        batch.invalidate_cache()
        self.assertEqual(
            {x.profile_id: x.amount for x in batch.profile_report},
            {self.ict3Y: 1200, self.car5y: 2000},
        )
        # Test view moves
        # 3 account.move
        res = batch.open_moves()
        self.assertEqual(len(res["domain"][0][2]), 3)
        # 6 account.move.line
        res = batch.open_move_lines()
        self.assertEqual(len(res["domain"][0][2]), 6)

    @freeze_time("2000-12-31")
    def test_02_asset_compute_batch_delay_compute(self):
        # Confirm 2 assets
        self.ict0.validate()
        self.assertEqual(self.ict0.depreciation_line_ids[1].amount, 500)
        self.vehicle0.validate()
        self.assertEqual(self.vehicle0.depreciation_line_ids[1].amount, 2000)
        # Compute Asset, with delay
        wiz = self._create_compute_wizard(use_batch=True, delay_compute=True)
        res = wiz.asset_compute()
        batch = self.env["account.asset.compute.batch"].browse(res["res_id"])
        self.assertEqual(batch.state, "draft")
        self.assertEqual(batch.depre_amount, 0)
        # Batch is still draft, require to click compute
        batch.action_compute()
        self.assertEqual(batch.state, "computed")
        self.assertEqual(batch.depre_amount, 2500)

    @freeze_time("2000-12-31")
    def test_03_asset_compute_batch_delay_compute_delay_post(self):
        # Confirm 2 assets
        self.ict0.validate()
        self.assertEqual(self.ict0.depreciation_line_ids[1].amount, 500)
        self.vehicle0.validate()
        self.assertEqual(self.vehicle0.depreciation_line_ids[1].amount, 2000)
        # Compute Asset, with delay
        wiz = self._create_compute_wizard(use_batch=True, delay_compute=True)
        res = wiz.asset_compute()
        batch = self.env["account.asset.compute.batch"].browse(res["res_id"])
        self.assertEqual(batch.state, "draft")
        self.assertEqual(batch.depre_amount, 0)
        batch.delay_post = True
        # Batch is still draft, require to click compute
        batch.action_compute()
        self.assertEqual(batch.state, "computed")
        self.assertEqual(batch.depre_amount, 2500)
        # All account.move is flag as auto_post = True, and state in draft
        self.assertTrue(all(batch.move_line_ids.mapped("move_id.auto_post")))
        self.assertTrue(
            all(
                state == "draft"
                for state in batch.move_line_ids.mapped("move_id.state")
            )
        )

    @freeze_time("2000-12-31")
    def test_04_asset_compute_batch_auto_compute(self):
        # Confirm 2 assets
        self.ict0.validate()
        self.assertEqual(self.ict0.depreciation_line_ids[1].amount, 500)
        self.vehicle0.validate()
        self.assertEqual(self.vehicle0.depreciation_line_ids[1].amount, 2000)
        # Compute Asset, with delay
        wiz = self._create_compute_wizard(use_batch=True, delay_compute=True)
        res = wiz.asset_compute()
        batch = self.env["account.asset.compute.batch"].browse(res["res_id"])
        self.assertEqual(batch.state, "draft")
        self.assertEqual(batch.depre_amount, 0)
        batch.auto_compute = True
        # Batch will be posted by cron job
        batch._autocompute_draft_batches()
        self.assertEqual(batch.state, "computed")
        self.assertEqual(batch.depre_amount, 2500)
