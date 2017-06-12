# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.tests.common as common


class TestAssetManagementXls(common.TransactionCase):

    def setUp(self):
        super(TestAssetManagementXls, self).setUp()
        ctx = {'xls_export': 1}
        self.act_report = self.env['ir.actions.report.xml'].with_context(ctx)
        self.wiz_model = self.env['wiz.account.asset.report']
        self.xls_report_name = 'account.asset.xls'
        fy_id = self.env['account.fiscalyear'].find()
        wiz_vals = {'fiscalyear_id': fy_id}
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
        self.assertEqual(report_xls[1], 'xls')
