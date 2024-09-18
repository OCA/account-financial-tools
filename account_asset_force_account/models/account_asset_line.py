# Copyright 2024 Bernat Obrador(APSL-Nagarro)<bobrador@apsl.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAssetLine(models.Model):
    _inherit = "account.asset.line"

    def _setup_move_line_data(self, depreciation_date, account, ml_type, move):
        res = super()._setup_move_line_data(depreciation_date, account, ml_type, move)
        asset = self.asset_id
        if ml_type == "depreciation" and asset.account_depreciation_id:
            res["account_id"] = asset.account_depreciation_id.id
        if ml_type == "expense" and asset.account_expense_depreciation_id:
            res["account_id"] = asset.account_expense_depreciation_id.id
        return res
