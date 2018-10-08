# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
from odoo import tools
from odoo.modules.module import get_resource_path


class TestAssetManagementXls(SavepointCase):

    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(cls.cr, module,
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           cls.registry._assertion_report)

    @classmethod
    def setUpClass(cls):
        super(TestAssetManagementXls, cls).setUpClass()

        cls._load('account', 'test', 'account_minimal_test.xml')
        cls._load('account_asset_management', 'tests',
                  'account_asset_test_data.xml')
        module = __name__.split('addons.')[1].split('.')[0]
        cls.xls_report_name = '{}.asset_report_xls'.format(module)
        cls.wiz_model = cls.env['wiz.account.asset.report']
        fy = cls.env.ref('account_asset_management.date_range_fy')
        wiz_vals = {'date_range_id': fy.id}
        cls.xls_report = cls.wiz_model.create(wiz_vals)
        cls.report_action = cls.xls_report.xls_export()

    def test_01_action_xls(self):
        """ Check report XLS action """
        self.assertDictContainsSubset(
            {'type': 'ir.actions.report',
             'report_type': 'xlsx',
             'report_name': self.xls_report_name},
            self.report_action)
