# Copyright 2009-2018 Noviat.
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
        module = __name__.split('addons.')[1].split('.')[0]
        self.xls_report_name = '{}.asset_report_xls'.format(module)
        self.wiz_model = self.env['wiz.account.asset.report']
        fy = self.env.ref('account_asset_management.date_range_fy')
        wiz_vals = {'date_range_id': fy.id}
        self.xls_report = self.wiz_model.create(wiz_vals)
        self.report_action = self.xls_report.xls_export()

    def test_01_action_xls(self):
        """ Check report XLS action """
        self.assertDictContainsSubset(
            {'type': 'ir.actions.report',
             'report_type': 'xlsx',
             'report_name': self.xls_report_name},
            self.report_action)
