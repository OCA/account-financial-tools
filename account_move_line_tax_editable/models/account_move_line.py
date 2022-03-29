# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    is_tax_editable = fields.Boolean(
        string="Is tax data editable?", compute="_compute_is_tax_editable"
    )

    @api.depends("move_id.state")
    def _compute_is_tax_editable(self):
        for rec in self:
            rec.is_tax_editable = rec.move_id.state == "draft"

    force_tax_line_id = fields.Many2one(
        "account.tax",
        string="Force Originator Tax",
        ondelete="restrict",
        help="When giving a value to this field (only appears in edit mode), Originator"
        " tax will take its value. If non is set, Originator tax will maintain its value",
        readonly=False,
    )

    @api.depends(
        "tax_repartition_line_id.invoice_tax_id",
        "tax_repartition_line_id.refund_tax_id",
        "force_tax_line_id",
    )
    def _compute_tax_line_id(self):
        forced_lines = self.filtered(lambda r: r.force_tax_line_id)
        for rec in forced_lines:
            rec.tax_line_id = rec.force_tax_line_id
        return super(AccountMoveLine, self - forced_lines)._compute_tax_line_id()
