# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    display_generate_epd_move = fields.Boolean(
        compute="_compute_display_generate_epd_move",
    )
    generated_epd_move_id = fields.Many2one("account.move", readonly=True)
    generated_epd_move_not_reconciled = fields.Boolean(
        compute="_compute_generated_epd_move_not_reconciled"
    )

    @api.depends(
        "generated_epd_move_id",
        "move_type",
        "state",
        "line_ids.display_type",
        "line_ids.discount_amount_currency",
    )
    def _compute_display_generate_epd_move(self):
        for move in self:
            move.display_generate_epd_move = (
                any(
                    not move.company_currency_id.is_zero(line.discount_amount_currency)
                    for line in move.line_ids
                    if line.display_type == "payment_term"
                )
                and move.state == "posted"
                and move.move_type in ("out_invoice", "in_invoice")
                and not move.generated_epd_move_id
            )

    @api.depends(
        "generated_epd_move_id",
        "line_ids.matched_debit_ids",
        "line_ids.matched_credit_ids",
    )
    def _compute_generated_epd_move_not_reconciled(self):
        for move in self:
            epd_move = move.generated_epd_move_id
            if not epd_move:
                move.generated_epd_move_not_reconciled = False
                continue

            epd_rec_pay_line = epd_move.line_ids.filtered(
                lambda li: li.account_id.account_type
                in ("asset_receivable", "liability_payable")
            )
            invoice_pay_term_lines = move.line_ids.filtered(
                lambda li: li.account_id.account_type
                in ("asset_receivable", "liability_payable")
            )
            reconciled_lines = (
                invoice_pay_term_lines.matched_debit_ids.debit_move_id
                | invoice_pay_term_lines.matched_credit_ids.credit_move_id
            )
            move.generated_epd_move_not_reconciled = not bool(
                epd_rec_pay_line & reconciled_lines
            )
