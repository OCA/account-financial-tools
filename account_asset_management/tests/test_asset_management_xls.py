# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import SavepointCase


class TestAssetManagementXls(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAssetManagementXls, cls).setUpClass()

        module = __name__.split("addons.")[1].split(".")[0]
        cls.xls_report_name = "{}.asset_report_xls".format(module)
        cls.wiz_model = cls.env["wiz.account.asset.report"]
        cls.company = cls.env.ref("base.main_company")
        asset_group_id = cls.wiz_model._default_asset_group_id()
        fy_dates = cls.company.compute_fiscalyear_dates(fields.date.today())

        wiz_vals = {
            "asset_group_id": asset_group_id,
            "date_from": fy_dates["date_from"],
            "date_to": fy_dates["date_to"],
        }
        cls.xls_report = cls.wiz_model.create(wiz_vals)
        cls.report_action = cls.xls_report.xls_export()

    def test_01_action_xls(self):
        """ Check report XLS action """
        self.assertGreaterEqual(
            self.report_action.items(),
            {
                "type": "ir.actions.report",
                "report_type": "xlsx",
                "report_name": self.xls_report_name,
            }.items(),
        )
