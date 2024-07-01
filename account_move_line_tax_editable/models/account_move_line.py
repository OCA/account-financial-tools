# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_tax_editable = fields.Boolean(
        string="Is tax data editable?", compute="_compute_is_tax_editable"
    )

    tax_line_id = fields.Many2one(inverse="_inverse_tax_line_id")

    @api.depends("move_id.state")
    def _compute_is_tax_editable(self):
        for rec in self:
            rec.is_tax_editable = rec.move_id.state == "draft"

    def _inverse_tax_line_id(self):
        for rec in self:
            repartition_type = rec.tax_repartition_line_id.repartition_type or "tax"
            factor_percent = rec.tax_repartition_line_id.factor_percent or 100
            has_account = bool(rec.tax_repartition_line_id.account_id)
            if rec.move_id.move_type in ("out_refund", "in_refund"):
                repartition_lines = rec.tax_line_id.refund_repartition_line_ids
            else:
                repartition_lines = rec.tax_line_id.invoice_repartition_line_ids
            lines = repartition_lines.filtered(
                lambda rl,
                repartition_type=repartition_type,
                factor_percent=factor_percent: rl.repartition_type == repartition_type
                and rl.factor_percent == factor_percent
            )
            if len(lines) > 1:
                lines = (
                    lines.filtered(
                        lambda rl, has_account=has_account: rl.repartition_type
                        == "base"
                        or has_account is bool(rl.account_id)
                    )[:1]
                    or lines[:1]
                )
            elif not lines:
                lines = repartition_lines.filtered(
                    lambda rl, repartition_type=repartition_type: rl.repartition_type
                    == repartition_type
                )[:1]
            rec.tax_repartition_line_id = lines
