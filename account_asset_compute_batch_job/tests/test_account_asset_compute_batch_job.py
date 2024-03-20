# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.account_asset_compute_batch.tests.test_account_asset_compute_batch import (
    TestAssetComputeBatch,
)


@tagged("post_install", "-at_install")
class TestAssetComputeBatchJob(TestAssetComputeBatch):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_asset_compute_batch_job(self):
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
        # Batch will be posted by cron job
        self.assertFalse(batch.job_state)
        batch.with_context(compute_batch_job=1).action_compute_job()
        self.assertEqual(batch.job_state, "pending")
        # Check queue job should be 1
        action = batch.open_queue_job()
        self.assertEqual(action["domain"][0][2], batch.job_current.ids)
