# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, tools
from odoo.modules.module import get_resource_path
from odoo.tests.common import SavepointCase


class TestAssetManagementXls(SavepointCase):
    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(
            cls.cr,
            module,
            get_resource_path(module, *args),
            {},
            "init",
            False,
            "test",
            cls.registry._assertion_report,
        )

    @classmethod
    def setUpClass(cls):
        super(TestAssetManagementXls, cls).setUpClass()

        cls._load("account", "test", "account_minimal_test.xml")
        cls._load("account_asset_management", "tests", "account_asset_test_data.xml")
        module = __name__.split("addons.")[1].split(".")[0]
        cls.xls_report_name = "{}.asset_report_xls".format(module)
        cls.wiz_model = cls.env["wiz.account.asset.report"]
        cls.company = cls.env.ref("base.main_company")
        # Ensure we have something to report on
        cls.env.ref("account_asset_management." "account_asset_asset_ict0").validate()
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
        """ Check report XLS action and generate report """
        self.assertDictContainsSubset(
            {
                "type": "ir.actions.report",
                "report_type": "xlsx",
                "report_name": self.xls_report_name,
            },
            self.report_action,
        )
        model = self.env["report.%s" % self.report_action["report_name"]].with_context(
            active_model=self.xls_report._name, **self.report_action["context"]
        )
        model.create_xlsx_report(self.xls_report.ids, data=self.report_action["data"])
