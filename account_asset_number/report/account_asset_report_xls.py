# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AssetReportXlsx(models.AbstractModel):
    _inherit = "report.account_asset_management.asset_report_xls"

    def _get_asset_template(self):
        res = super()._get_asset_template()
        res.update(
            {
                "number": {
                    "header": {"type": "string", "value": self._("Number")},
                    "asset": {
                        "type": "string",
                        "value": self._render("asset.number or ''"),
                    },
                    "width": 20,
                }
            }
        )
        return res
