# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_realtime_out_lines_vals(self):
        res = super()._stock_account_prepare_realtime_out_lines_vals()
        origin_lines = self.env["account.move.line"].browse(
            [vals["cogs_origin_id"] for vals in res if vals.get("cogs_origin_id")]
        )
        repair_per_line = {line.id: line.repair_order_id.id for line in origin_lines}
        for vals in res:
            repair_order_id = repair_per_line.get(vals.get("cogs_origin_id"))
            if repair_order_id:
                vals["repair_order_id"] = repair_order_id
        return res
