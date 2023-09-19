# Copyright 2021 Ecosoft Co., Ltd. <http://ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    asset_count = fields.Integer(compute="_compute_asset_count")

    def _compute_asset_count(self):
        for rec in self:
            moves = self.env["account.move"].search(
                [("stock_move_id", "in", rec.move_lines.ids)]
            )
            rec.asset_count = sum(moves.mapped("asset_count"))

    def action_view_assets(self):
        moves = self.env["account.move"].search(
            [("stock_move_id", "in", self.move_lines.ids)]
        )
        assets = (
            self.env["account.asset.line"]
            .search([("move_id", "in", moves.ids)])
            .mapped("asset_id")
        )
        action = self.env.ref("account_asset_management.account_asset_action")
        action_dict = action.sudo().read()[0]
        if len(assets) == 1:
            res = self.env.ref(
                "account_asset_management.account_asset_view_form", False
            )
            action_dict["views"] = [(res and res.id or False, "form")]
            action_dict["res_id"] = assets.id
        elif assets:
            action_dict["domain"] = [("id", "in", assets.ids)]
        else:
            action_dict = {"type": "ir.actions.act_window_close"}
        return action_dict
