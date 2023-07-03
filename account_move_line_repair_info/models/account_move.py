# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_interim_account_line_vals(self, line, move, debit_interim_account):
        res = super()._prepare_interim_account_line_vals(
            line, move, debit_interim_account
        )
        if len(line.repair_line_ids) == 1:
            res.update(
                {
                    "repair_order_id": line.repair_line_ids.repair_id.id,
                }
            )
        if len(line.repair_fee_ids) == 1:
            res.update(
                {
                    "repair_order_id": line.repair_fee_ids.repair_id.id,
                }
            )
        return res

    def _prepare_expense_account_line_vals(self, line, move, debit_interim_account):
        res = super()._prepare_expense_account_line_vals(
            line, move, debit_interim_account
        )
        if len(line.repair_line_ids) == 1:
            res.update(
                {
                    "repair_order_id": line.repair_line_ids.repair_id.id,
                }
            )
        if len(line.repair_fee_ids) == 1:
            res.update(
                {
                    "repair_order_id": line.repair_fee_ids.repair_id.id,
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
