# Copyright 2016-19 ACSONE SA/NV
# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
from datetime import date

from dateutil import relativedelta

from odoo.tests.common import TransactionCase

from odoo.addons.queue_job.job import Job


class TestAccountAssetBatchCompute(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wiz_obj = cls.env["account.asset.compute"]
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test account",
                "code": "TAC",
                "account_type": "liability_payable",
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test Journal", "code": "TJ", "type": "general"}
        )
        cls.profile = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.account.id,
                "account_asset_id": cls.account.id,
                "account_depreciation_id": cls.account.id,
                "journal_id": cls.journal.id,
                "name": "Test",
            }
        )
        cls.asset01 = cls.asset_model.create(
            {
                "name": "test asset",
                "profile_id": cls.profile.id,
                "purchase_value": 1000,
                "salvage_value": 0,
                "date_start": time.strftime("2003-01-01"),
                "method_time": "year",
                "method_number": 1,
                "method_period": "month",
                "prorata": False,
            }
        )
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        cls.nextmonth = first_day_of_month + relativedelta.relativedelta(months=1)
        cls.asset01.date_start = first_day_of_month

    def test_no_batch_processing(self):
        wiz = self.wiz_obj.create(
            {"batch_processing": False, "date_end": self.nextmonth}
        )
        # I check if this asset is draft
        self.assertEqual(self.asset01.state, "draft")
        # I confirm this asset
        self.asset01.validate()
        # I check if this asset is running
        self.assertEqual(self.asset01.state, "open")
        self.asset01.compute_depreciation_board()
        # I check that there is no depreciation line
        depreciation_line = self.asset01.depreciation_line_ids.filtered(
            lambda r: r.type == "depreciate" and r.move_id
        )
        self.assertTrue(len(depreciation_line) == 0)
        wiz.asset_compute()
        depreciation_line = self.asset01.depreciation_line_ids.filtered(
            lambda r: r.type == "depreciate" and r.move_id
        )
        self.assertTrue(len(depreciation_line) == 1)

    def test_batch_processing(self):
        wiz = self.wiz_obj.create(
            {"batch_processing": True, "date_end": self.nextmonth}
        )
        # I check if this asset is draft
        self.assertEqual(self.asset01.state, "draft")
        # I confirm this asset
        self.asset01.validate()
        # I check if this asset is running
        self.assertEqual(self.asset01.state, "open")
        self.asset01.compute_depreciation_board()
        # I check that there is no depreciation line
        depreciation_line = self.asset01.depreciation_line_ids.filtered(
            lambda r: r.type == "depreciate" and r.move_id
        )
        self.assertTrue(len(depreciation_line) == 0)
        wiz.with_context(test_queue_job_no_delay=False).asset_compute()
        depreciation_line = self.asset01.depreciation_line_ids.filtered(
            lambda r: r.type == "depreciate" and r.move_id
        )
        self.assertTrue(len(depreciation_line) == 0)
        job_name = "Creating jobs to create moves for assets to %s" % (self.nextmonth)
        jobs = self.env["queue.job"].search(
            [("name", "=", job_name)], order="date_created desc", limit=1
        )
        self.assertEqual(
            jobs.job_function_id,
            self.env.ref(
                "account_asset_batch_compute."
                "job_function_account_asset_compute_asset_compute"
            ),
        )
        self.assertTrue(len(jobs) == 1)
        job = Job.load(self.env, jobs.uuid)
        # perform job
        job.perform()
        depreciation_line = self.asset01.depreciation_line_ids.filtered(
            lambda r: r.type == "depreciate" and r.move_id
        )
        self.assertTrue(len(depreciation_line) == 0)
        job_name = "Creating move for asset with id {} to {}".format(
            self.asset01.id,
            self.nextmonth,
        )
        jobs = self.env["queue.job"].search(
            [("name", "=", job_name)], order="date_created desc", limit=1
        )
        self.assertTrue(len(jobs) == 1)
        self.assertEqual(
            jobs.job_function_id,
            self.env.ref(
                "account_asset_batch_compute.job_function_account_asset_compute_entries"
            ),
        )
        job = Job.load(self.env, jobs.uuid)
        job.perform()
        depreciation_line = self.asset01.depreciation_line_ids.filtered(
            lambda r: r.type == "depreciate" and r.move_id
        )
        self.assertEqual(len(depreciation_line), 1)
