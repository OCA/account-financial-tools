# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountClearancePlanLine(models.TransientModel):
    _inherit = "account.clearance.plan.line"

    @api.model
    def _default_payment_mode_allowed(self):
        if self._context.get("active_model") in (
            "account.invoice",
            "account.move.line",
        ):
            lines = self.env[self._context.get("active_model")].browse(
                self._context.get("active_ids")
            )
            types = lines.mapped("account_id.user_type_id.type")
            if all(t == "receivable" for t in types):
                return self.env["account.payment.mode"].search(
                    [("payment_type", "=", "inbound")]
                )
            if all(t == "payable" for t in types):
                return self.env["account.payment.mode"].search(
                    [("payment_type", "=", "outbound")]
                )
            return self.env["account.payment.mode"].search([])

    @api.model
    def _default_mandate_allowed(self):
        if self._context.get("active_model") in (
            "account.invoice",
            "account.move.line",
        ):
            lines = self.env[self._context.get("active_model")].browse(
                self._context.get("active_ids")
            )
            partner_id = lines.mapped("partner_id.commercial_partner_id")
            return self.env["account.banking.mandate"].search(
                [("partner_id", "=", partner_id.id), ("state", "=", "valid")]
            )

    payment_mode_allowed_ids = fields.Many2many(
        "account.payment.mode",
        default=_default_payment_mode_allowed,
        store=False,
        readonly=True,
    )
    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        required=True,
        domain="[('id', 'in', payment_mode_allowed_ids)]",
    )
    mandate_allowed_ids = fields.Many2many(
        "account.banking.mandate",
        default=_default_mandate_allowed,
        store=False,
        readonly=True,
    )
    mandate_id = fields.Many2one(
        "account.banking.mandate",
        string="Direct Debit Mandate",
        domain="[('id', 'in', mandate_allowed_ids)]",
    )
    mandate_required = fields.Boolean(
        related="payment_mode_id.payment_method_id.mandate_required",
        readonly=True,
    )

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self._context.get("active_model") not in (
            "account.invoice",
            "account.move.line",
        ):
            return rec
        active_records = self.env[self._context.get("active_model")].browse(
            self._context.get("active_ids")
        )
        payment_mode_ids = active_records.mapped("payment_mode_id")
        if len(payment_mode_ids) == 1:
            rec.update({"payment_mode_id": payment_mode_ids.id})
        return rec


class AccountClearancePlan(models.TransientModel):
    _inherit = "account.clearance.plan"

    def _get_move_line_vals(self, move, line):
        res = super()._get_move_line_vals(move, line)
        res.update(
            {
                "payment_mode_id": line.payment_mode_id.id,
                "mandate_id": line.mandate_id.id,
            }
        )
        return res
