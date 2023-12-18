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
        self, name, date, remaining_amount_currency, currency, debit, credit, account
    ):
        return [
            {
                "name": name,
                "date_maturity": date,
                "amount_currency": remaining_amount_currency,
                "currency_id": currency.id,
                "debit": debit,
                "credit": credit,
                "partner_id": self.partner_id.id,
                "account_id": account.id,
            }
        ]

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        if self.env.context.get("netting"):
            moves = self.env["account.move"].browse(self.env.context.get("active_ids"))
            ml_reconciled = moves.mapped("line_ids").filtered(
                lambda l: l.account_type in ("asset_receivable", "liability_payable")
                and not l.reconciled
            )

            line_vals_list = []
            remaining_amount = remaining_amount_currency = 0.0

            # Write-off
            write_off_line_vals = write_off_line_vals or []

            if self.payment_type == "inbound":
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == "outbound":
                # Send money.
                liquidity_amount_currency = -self.amount
            else:
                liquidity_amount_currency = 0.0

            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )

            move_lines = sorted(
                ml_reconciled, key=lambda k: (abs(k["amount_residual"]))
            )

            for i, line in enumerate(move_lines):
                # Last line
                if i == len(move_lines) - 1 and not write_off_line_vals:
                    amount_total_currency = (
                        liquidity_amount_currency - remaining_amount_currency
                    )
                    amount_total = liquidity_balance - remaining_amount
                    line_vals_list += self._get_move_line_vals_netting(
                        line.move_id.name,
                        self.date,
                        abs(amount_total_currency)
                        if amount_total_currency < 0.0
                        else -amount_total_currency,
                        line.currency_id,
                        abs(amount_total) if amount_total < 0.0 else 0.0,
                        amount_total if amount_total > 0.0 else 0.0,
                        line.account_id,
                    )
                    break

                debit = -line.amount_residual if line.amount_residual < 0.0 else 0.0
                credit = line.amount_residual if line.amount_residual > 0.0 else 0.0
                amount_residual_currency = -line.amount_residual_currency

                # Split debit line for case AP > AR
                if (
                    liquidity_balance < 0.0
                    and line.account_type == "liability_payable"
                    and remaining_amount > 0.0
                    and remaining_amount < abs(line.amount_residual)
                ):
                    line_vals_list += self._get_move_line_vals_netting(
                        line.move_id.name,
                        self.date,
                        remaining_amount_currency,
                        line.currency_id,
                        remaining_amount,
                        0.0,
                        line.account_id,
                    )
                    debit = line.amount_residual + remaining_amount
                    credit = 0.0
                    amount_residual_currency = -(
                        line.amount_residual_currency + remaining_amount_currency
                    )
                    # split line
                    if not write_off_line_vals and abs(amount_residual_currency) >= abs(
                        liquidity_amount_currency
                    ):
                        amount_residual_currency = -liquidity_amount_currency
                        debit = liquidity_balance
                        line_vals_list += self._get_move_line_vals_netting(
                            line.move_id.name,
                            self.date,
                            amount_residual_currency,
                            line.currency_id,
                            abs(debit),
                            abs(credit),
                            line.account_id,
                        )
                        break

                # Split credit line case AP < AR
                if (
                    liquidity_balance > 0.0
                    and line.account_type == "asset_receivable"
                    and remaining_amount < 0.0
                    and abs(remaining_amount) < line.amount_residual
                ):
                    line_vals_list += self._get_move_line_vals_netting(
                        line.move_id.name,
                        self.date,
                        remaining_amount_currency,
                        line.currency_id,
                        0.0,
                        abs(remaining_amount),
                        line.account_id,
                    )
                    debit = 0.0
                    credit = line.amount_residual + remaining_amount
                    amount_residual_currency = -(
                        line.amount_residual_currency + remaining_amount_currency
                    )
                    # split line
                    if not write_off_line_vals and abs(amount_residual_currency) >= abs(
                        liquidity_amount_currency
                    ):
                        amount_residual_currency = -liquidity_amount_currency
                        credit = liquidity_balance
                        line_vals_list += self._get_move_line_vals_netting(
                            line.move_id.name,
                            self.date,
                            amount_residual_currency,
                            line.currency_id,
                            abs(debit),
                            abs(credit),
                            line.account_id,
                        )
                        break

                line_vals_list += self._get_move_line_vals_netting(
                    line.move_id.name,
                    self.date,
                    amount_residual_currency,
                    line.currency_id,
                    abs(debit),
                    abs(credit),
                    line.account_id,
                )
                remaining_amount_currency += line.amount_residual_currency
                remaining_amount += line.amount_residual

            # Liquidity line.
            line_vals_list += self._get_move_line_vals_netting(
                self.ref,
                self.date,
                liquidity_amount_currency,
                self.currency_id,
                liquidity_balance if liquidity_balance > 0.0 else 0.0,
                -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                self.outstanding_account_id,
            )
            return line_vals_list + write_off_line_vals
        return super()._prepare_move_line_default_vals(write_off_line_vals)
