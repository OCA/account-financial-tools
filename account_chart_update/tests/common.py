# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("-at_install", "post_install")
class TestAccountChartUpdateCommon(BaseCommon):
    def _get_model_data(self, record):
        return self.env["ir.model.data"].search(
            [("model", "=", record._name), ("res_id", "=", record.id)]
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test account_chart_update company",
                "country_id": cls.env.ref("base.us").id,
            }
        )
        template = cls.env["account.chart.template"]
        template.try_loading("generic_coa", cls.company)
        cls.chart_template_data = template._get_chart_template_data("generic_coa")
        # We delete the records so that we can later delete the linked data
        moves = cls.env["account.move"].search(
            [
                ("company_id", "=", cls.company.id),
            ]
        )
        moves.filtered(lambda x: x.state == "posted").button_draft()
        moves.unlink()
        # Prepare wizard
        cls.wizard_obj = cls.env["wizard.update.charts.accounts"]
        cls.wizard_vals = {
            "company_id": cls.company.id,
            "chart_template": "generic_coa",
            "code_digits": 6,
        }
