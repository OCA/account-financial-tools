# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        res = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        for i, vals in enumerate(res):
            if (
                not vals.get("move_id", False)
                or not vals.get("product_id", False)
                or not vals.get("quantity", False)
            ):
                continue
            am = self.env["account.move"].browse(vals["move_id"])
            repair_line = am.invoice_line_ids.filtered(
                lambda il, vals=vals: il.product_id.id == vals["product_id"]
                and il.quantity == vals["quantity"]
            )
            repair_order = repair_line.mapped("repair_order_id")
            if len(repair_order) == 1:
                res[i].update(
                    {
                        "repair_order_id": repair_order.id,
                    }
                )
        return res
