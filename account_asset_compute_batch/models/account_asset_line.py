# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAssetLine(models.Model):
    _inherit = "account.asset.line"

    def _setup_move_line_data(self, depreciation_date, account, ml_type, move):
        move_line_data = super()._setup_move_line_data(
            depreciation_date, account, ml_type, move
        )
        if self.env.context.get("compute_batch_id"):
            move_line_data["compute_batch_id"] = self.env.context["compute_batch_id"]
        return move_line_data
