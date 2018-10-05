# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.tests.common as common
from odoo import tools
from odoo.modules.module import get_resource_path


class TestAssetManagementXls(common.TransactionCase):

    def _load(self, module, *args):
        tools.convert_file(self.cr, module,
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           self.registry._assertion_report)

    def setUp(self):
        super(TestAssetManagementXls, self).setUp()

        self._load('account', 'test', 'account_minimal_test.xml')
        self._load('account_asset_management', 'tests',
                   'account_asset_test_data.xml')

        ctx = {'xlsx_export': 1}
        self.act_report = self.env['ir.actions.report.xml'].with_context(ctx)
        self.wiz_model = self.env['wiz.account.asset.report']
        self.xls_report_name = 'account.asset.xlsx'
        fy = self.env.ref('account_asset_management.date_range_fy')
        wiz_vals = {'date_range_id': fy.id}
        self.xls_report = self.wiz_model.create(wiz_vals)
        self.report_action = self.xls_report.xls_export()
        self.render_dict = self.report_action['datas']

    def test_01_action_xls(self):
        """ Check report XLS action """
        self.assertDictContainsSubset(
            {'type': 'ir.actions.report.xml',
             'report_name': self.xls_report_name},
            self.report_action)

    def test_02_render_xls(self):
        """ Check XLS rendering """
        report_xls = self.act_report.render_report(
            self.xls_report.ids,
            self.xls_report_name,
            self.render_dict)
        self.assertGreaterEqual(len(report_xls[0]), 1)
        self.assertEqual(report_xls[1], 'xlsx')
