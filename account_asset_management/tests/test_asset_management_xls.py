# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time

from odoo import fields

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestAssetManagementXls(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super(TestAssetManagementXls, cls).setUpClass()

        module = __name__.split("addons.")[1].split(".")[0]
        cls.xls_report_name = "{}.asset_report_xls".format(module)
        cls.wiz_model = cls.env["wiz.account.asset.report"]
        cls.company = cls.env.ref("base.main_company")
        # Ensure we have something to report on
        group_fa = cls.env["account.asset.group"].create(
            {
                "name": "Fixed Assets",
                "code": "FA",
            }
        )
        group_tfa = cls.env["account.asset.group"].create(
            {
                "name": "Tangible Fixed Assets",
                "code": "TFA",
                "parent_id": group_fa.id,
            }
        )
        ict3Y = cls.env["account.asset.profile"].create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "group_ids": [(6, 0, group_tfa.ids)],
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Hardware - 3 Years",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        cls.env["account.asset"].create(
            {
                "state": "draft",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
                "name": "Laptop",
                "code": "PI00101",
                "purchase_value": 1500.0,
                "profile_id": ict3Y.id,
                "date_start": time.strftime("%Y-01-01"),
            }
        ).validate()
        fy_dates = cls.company.compute_fiscalyear_dates(fields.date.today())

        wiz_vals = {
            "asset_group_id": group_fa.id,
            "date_from": fy_dates["date_from"],
            "date_to": fy_dates["date_to"],
        }
        cls.xls_report = cls.wiz_model.create(wiz_vals)
        cls.report_action = cls.xls_report.xls_export()

    def test_01_action_xls(self):
        """ Check report XLS action and generate report """
        self.assertGreaterEqual(
            self.report_action.items(),
            {
                "type": "ir.actions.report",
                "report_type": "xlsx",
                "report_name": self.xls_report_name,
            }.items(),
        )
        model = self.env["report.%s" % self.report_action["report_name"]].with_context(
            active_model=self.xls_report._name, **self.report_action["context"]
        )
        model.create_xlsx_report(self.xls_report.ids, data=self.report_action["data"])
