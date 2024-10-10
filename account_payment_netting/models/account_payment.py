# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountPayments(models.Model):
    _inherit = "account.payment"

    netting = fields.Boolean(
        readonly=True,
        help="Technical field, as user select invoice that are both AR and AP",
    )

    def _synchronize_from_moves(self, changed_fields):
        if self.env.context.get("netting"):
            self = self.with_context(skip_account_move_synchronization=1)
        return super()._synchronize_from_moves(changed_fields)

    def _get_move_line_vals_netting(
        self, name, date, remaining_amount_currency, currency, account
    ):
        return [
            {
                "name": name,
                "date_maturity": date,
                "amount_currency": remaining_amount_currency,
                "currency_id": currency.id,
                "partner_id": self.partner_id.id,
                "account_id": account.id,
            }
        ]

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        if self.env.context.get("netting"):
            domain = [
                ("move_id", "in", self.env.context.get("active_ids", [])),
                ("account_type", "in", ["asset_receivable", "liability_payable"]),
                ("reconciled", "=", False),
            ]
            # Sort by amount
            # Inbound: AR > AP; loop AP first
            # Outbound: AP > AR; loop AR first
            ml_reconciled = self.env["account.move.line"].search(domain)
            if self.payment_type == "inbound":
                move_lines = sorted(
                    ml_reconciled, key=lambda k: (k.move_type, k.amount_residual)
                )
            else:
                move_lines = sorted(
                    ml_reconciled,
                    key=lambda k: (k.move_type, -abs(k.amount_residual)),
                    reverse=True,
                )

            line_vals_list = []
            liquidity_amount_currency = self.amount
            remaining_amount_currency = 0.0
            current_move_type = False

            # Write-off
            write_off_line_vals = write_off_line_vals or []

            for i, line in enumerate(move_lines):
                # AR > AP but line is AP, change sign to positive
                sign = (
                    1
                    if self.payment_type == "outbound"
                    and line.move_type == "in_invoice"
                    else -1
                )
                amount_residual_currency = line.amount_residual_currency
                # Last line
                if (
                    liquidity_amount_currency
                    and i == len(move_lines) - 1
                    and not write_off_line_vals
                ):
                    # For case netting with 1 move type
                    if (
                        liquidity_amount_currency > abs(amount_residual_currency)
                        and remaining_amount_currency <= amount_residual_currency
                    ):
                        amount_total_currency = abs(amount_residual_currency)
                    else:
                        amount_total_currency = liquidity_amount_currency + abs(
                            remaining_amount_currency
                        )
                    line_vals_list += self._get_move_line_vals_netting(
                        line.move_id.name,
                        self.date,
                        sign * amount_total_currency,
                        line.currency_id,
                        line.account_id,
                    )
                    break
                # Check if move_type is changed
                if current_move_type and current_move_type != line.move_type:
                    # Get min amount from remaining_amount_currency and amount_residual_currency
                    if not write_off_line_vals:
                        amount_remaining = min(
                            abs(remaining_amount_currency),
                            abs(amount_residual_currency),
                        )
                    else:
                        amount_remaining = abs(amount_residual_currency)

                    # No create lines if amount_remaining is 0
                    if not amount_remaining:
                        continue

                    # AR > AP but line is AP, change sign to positive
                    line_vals_list += self._get_move_line_vals_netting(
                        line.move_id.name,
                        self.date,
                        sign * amount_remaining,
                        line.currency_id,
                        line.account_id,
                    )
                    remaining_amount_currency = abs(remaining_amount_currency) - abs(
                        amount_remaining
                    )
                # First line or same move_type
                else:
                    current_move_type = line.move_type
                    line_vals_list += self._get_move_line_vals_netting(
                        line.move_id.name,
                        self.date,
                        -1 * amount_residual_currency,
                        line.currency_id,
                        line.account_id,
                    )
                    remaining_amount_currency += amount_residual_currency

            # Liquidity line.
            if liquidity_amount_currency:
                line_vals_list += self._get_move_line_vals_netting(
                    self.ref,
                    self.date,
                    liquidity_amount_currency
                    if self.payment_type == "inbound"
                    else -liquidity_amount_currency,
                    self.currency_id,
                    self.outstanding_account_id,
                )
            return line_vals_list + write_off_line_vals
        return super()._prepare_move_line_default_vals(write_off_line_vals)
