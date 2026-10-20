# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountClearancePlan(models.TransientModel):
    _inherit = "account.clearance.plan"

    payment_mode_filter_type_domain = fields.Char(
        compute="_compute_payment_mode_filter_type_domain"
    )
    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        string="Payment Mode",
        help="Payment mode applied to the clearance journal entry.",
    )
    mandate_id = fields.Many2one(
        "account.banking.mandate",
        string="Direct Debit Mandate",
        domain="[('partner_id', '=', partner_id), ('state', '=', 'valid')]",
    )
    mandate_required = fields.Boolean(
        related="payment_mode_id.payment_method_id.mandate_required",
        readonly=True,
    )

    @api.depends("mode")
    def _compute_payment_mode_filter_type_domain(self):
        for rec in self:
            rec.payment_mode_filter_type_domain = (
                "inbound" if rec.mode == "receivable" else "outbound"
            )

    @api.model
    def default_get(self, fields_list):
        rec = super().default_get(fields_list)
        move_lines = self.env["account.move.line"].browse(rec.get("move_line_ids", []))
        payment_modes = move_lines.mapped("move_id.payment_mode_id")
        if len(payment_modes) == 1:
            rec["payment_mode_id"] = payment_modes.id
        mandates = move_lines.mapped("move_id.mandate_id")
        if len(mandates) == 1:
            rec["mandate_id"] = mandates.id
        return rec

    def _get_move_vals(self):
        res = super()._get_move_vals()
        res["payment_mode_id"] = self.payment_mode_id.id
        res["mandate_id"] = self.mandate_id.id
        return res
