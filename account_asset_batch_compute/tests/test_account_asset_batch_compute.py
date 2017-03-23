# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo.modules.module import get_resource_path

from odoo.tests.common import TransactionCase
from datetime import date

from dateutil import relativedelta

from odoo.addons.queue_job.job import Job

DELAY2 = ('odoo.addons.account_asset_batch_compute.wizards.'
          'asset_depreciation_confirmation_wizard.async_asset_compute')
DELAY1 = ('odoo.addons.account_asset_batch_compute.models.'
          'account_asset_asset.async_compute_entries')


class TestAccountAssetBatchCompute(TransactionCase):

    def _load(self, module, *args):
        tools.convert_file(self.cr, module,
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           self.registry._assertion_report)

    def setUp(self):
        super(TestAccountAssetBatchCompute, self).setUp()
        self._load('account', 'test', 'account_minimal_test.xml')
        self._load('account_asset_management', 'demo',
                   'account_asset_demo.xml')
        self.wiz_obj = self.env['asset.depreciation.confirmation.wizard']
        self.asset01 = self.env.ref(
            'account_asset_management.account_asset_ict0')
        self.asset01.method_period = 'month'
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        self.nextmonth =\
            first_day_of_month + relativedelta.relativedelta(months=1)
        self.nextmonth = first_day_of_month + relativedelta.relativedelta(
            months=1)
        self.asset01.date_start = first_day_of_month

    def test_1(self):
        wiz = self.wiz_obj.create({'batch_processing': False,
                                   'date_end': self.nextmonth})
        # I check if this asset is draft
        self.assertEqual(self.asset01.state, 'draft')
        # I confirm this asset
        self.asset01.validate()
        # I check if this asset is running
        self.assertEqual(self.asset01.state, 'open')
        self.asset01.compute_depreciation_board()
        # I check that there is no depreciation line
        depreciation_line = self.asset01.depreciation_line_ids\
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 0)
        wiz.asset_compute()
        depreciation_line = self.asset01.depreciation_line_ids\
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 1)

    def test_2(self):
        wiz = self.wiz_obj.create({'batch_processing': True,
                                   'date_end': self.nextmonth})
        # I check if this asset is draft
        self.assertEqual(self.asset01.state, 'draft')
        # I confirm this asset
        self.asset01.validate()
        # I check if this asset is running
        self.assertEqual(self.asset01.state, 'open')
        self.asset01.compute_depreciation_board()
        # I check that there is no depreciation line
        depreciation_line = self.asset01.depreciation_line_ids\
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 0)
        wiz.asset_compute()
        depreciation_line = self.asset01.depreciation_line_ids \
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 0)
        jobs = self.env['queue.job'].search(
            [], order='date_created desc', limit=1)
        self.assertTrue(len(jobs) == 1)
        job = Job.load(self.env, jobs.uuid)
        job.perform()
        depreciation_line = self.asset01.depreciation_line_ids \
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 0)
        jobs = self.env['queue.job'].search(
            [], order='date_created desc', limit=1)
        self.assertTrue(len(jobs) == 1)
        job = Job.load(self.env, jobs.uuid)
        job.perform()
        depreciation_line = self.asset01.depreciation_line_ids \
            .filtered(lambda r: r.type == 'depreciate' and r.move_id)
        self.assertTrue(len(depreciation_line) == 1)
