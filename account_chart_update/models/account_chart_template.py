# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _get_chart_template_mapping(self, get_all=False):
        chart_template_mapping = super()._get_chart_template_mapping(get_all=get_all)
        if self.env.context.get("chart_template_only_installed"):
            return dict(
                (_template_code, template)
                for (_template_code, template) in chart_template_mapping.items()
                if template["installed"]
            )
        return chart_template_mapping
