# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


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
                lambda il: il.product_id.id == vals["product_id"]
                and il.quantity == vals["quantity"]
            )
            repair_order = repair_line.repair_fee_ids.mapped("repair_id")
            if len(repair_order) == 1:
                res[i].update(
                    {
                        "repair_order_id": repair_line.repair_fee_ids.repair_id.id,
                    }
                )
            repair_order = repair_line.repair_line_ids.mapped("repair_id")
            if len(repair_order) == 1:
                res[i].update(
                    {
                        "repair_order_id": repair_line.repair_line_ids.repair_id.id,
                    }
                )
        return res

    @api.model_create_multi
    def create(self, values):
        rline_model = self.env["repair.line"]
        fline_model = self.env["repair.fee"]
        rorder_model = self.env["repair.order"]
        for val in values:
            for invoice_line_ids in val.get("invoice_line_ids", []):
                line_val = invoice_line_ids[2]
                if line_val.get("repair_line_ids", []):
                    repair_line_ids = [
                        r[1] for r in line_val.get("repair_line_ids", [])
                    ]
                    rline = rline_model.browse(repair_line_ids)
                    rorder = rline.mapped("repair_id")
                    if len(rorder) == 1:
                        line_val.update(
                            {
                                "repair_order_id": rline.mapped("repair_id").id,
                            }
                        )
                if line_val.get("repair_fee_ids", False):
                    repair_fee_ids = [r[1] for r in line_val.get("repair_fee_ids", [])]
                    fline = fline_model.browse(repair_fee_ids)
                    rorder = fline.mapped("repair_id")
                    if len(rorder) == 1:
                        line_val.update(
                            {
                                "repair_order_id": fline.mapped("repair_id").id,
                            }
                        )
                if line_val.get("repair_ids", False):
                    repair_ids = [r[1] for r in line_val.get("repair_ids", [])]
                    rorder = rorder_model.browse(repair_ids)
                    if len(rorder) == 1:
                        line_val.update(
                            {
                                "repair_order_id": rorder.id,
                            }
                        )
        return super(AccountMove, self).create(values)


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    repair_order_id = fields.Many2one(
        comodel_name="repair.order",
        string="Repair Order",
        ondelete="set null",
        index=True,
        copy=False,
    )
