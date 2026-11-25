# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountLoanLine(models.Model):
    _inherit = "account.loan.line"

    extra_cost_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=False,
        store=True,
        compute="_compute_extra_cost_amount",
        help="Total amount of extra costs (insurance, fees...) for this "
        "installment. Each cost is booked on its own account in the journal "
        "entry to allow comparison with the lender's amortization table.",
    )
    is_manual_payment = fields.Boolean(
        readonly=True,
        help="Set on lines created by early-repayment or capital-increase "
        "wizards. Such lines are excluded from periodic extra cost computation.",
    )

    @api.depends(
        "loan_id.extra_cost_ids",
        "loan_id.extra_cost_ids.payment_type",
        "loan_id.extra_cost_ids.calculation_method",
        "loan_id.extra_cost_ids.amount",
        "loan_id.extra_cost_ids.rate",
        "pending_principal_amount",
        "sequence",
        "is_manual_payment",
    )
    def _compute_extra_cost_amount(self):
        for record in self:
            if record.is_manual_payment:
                record.extra_cost_amount = 0.0
                continue
            total = 0.0
            for cost in record.loan_id.extra_cost_ids.filtered(
                lambda c: c.payment_type == "periodic"
            ):
                total += cost._compute_periodic_amount(record)
            record.extra_cost_amount = total

    @api.depends("extra_cost_amount")
    def _compute_payment_amount(self):
        res = super()._compute_payment_amount()
        for rec in self:
            rec.payment_amount += rec.extra_cost_amount
        return res

    @api.depends("extra_cost_amount")
    def _compute_principal_amount(self):
        res = super()._compute_principal_amount()
        for rec in self:
            rec.principal_amount -= rec.extra_cost_amount
        return res

    @api.depends("extra_cost_amount")
    def _compute_amounts(self):
        res = super()._compute_amounts()
        for rec in self:
            rec.final_pending_principal_amount += rec.extra_cost_amount
        return res

    def _check_amount(self):
        res = super()._check_amount()
        self._compute_extra_cost_amount()
        if self.extra_cost_amount:
            principal = self.payment_amount - self.interests_amount
            self.payment_amount = self.currency_id.round(
                self.payment_amount + self.extra_cost_amount
            )
            self.principal_amount = principal
        return res

    def _check_move_amount(self):
        res = super()._check_move_amount()
        periodic_extra_costs = self.loan_id.extra_cost_ids.filtered(
            lambda c: c.payment_type == "periodic"
        )
        if periodic_extra_costs:
            move_lines = self.move_ids.mapped("line_ids")
            extra_cost_lines = move_lines.filtered("loan_extra_cost_id")
            plain_lines = move_lines - extra_cost_lines
            interests_lines = plain_lines.filtered(
                lambda r: r.account_id == self.loan_id.interest_expenses_account_id
            )
            short_term_lines = plain_lines.filtered(
                lambda r: r.account_id == self.loan_id.short_term_loan_account_id
            )
            long_term_lines = plain_lines.filtered(
                lambda r: r.account_id == self.loan_id.long_term_loan_account_id
            )
            self.interests_amount = sum(interests_lines.mapped("debit")) - sum(
                interests_lines.mapped("credit")
            )
            self.long_term_principal_amount = sum(
                long_term_lines.mapped("debit")
            ) - sum(long_term_lines.mapped("credit"))
            self.extra_cost_amount = sum(extra_cost_lines.mapped("debit")) - sum(
                extra_cost_lines.mapped("credit")
            )
            self.payment_amount = (
                sum(short_term_lines.mapped("debit"))
                - sum(short_term_lines.mapped("credit"))
                + self.long_term_principal_amount
                + self.interests_amount
                + self.extra_cost_amount
            )
        return res

    def _move_line_vals(self, account=False):
        vals = super()._move_line_vals(account=account)
        if not self.extra_cost_amount:
            return vals
        st_account_id = self.loan_id.short_term_loan_account_id.id
        for line_vals in vals:
            if (
                line_vals.get("account_id") == st_account_id
                and not line_vals.get("name")
                and (line_vals.get("debit") or line_vals.get("credit"))
            ):
                if line_vals.get("debit"):
                    line_vals["debit"] -= self.extra_cost_amount
                else:
                    line_vals["credit"] += self.extra_cost_amount
                break
        for cost in self.loan_id.extra_cost_ids.filtered(
            lambda c: c.payment_type == "periodic"
        ):
            amount = cost._compute_periodic_amount(self)
            if amount:
                vals.append(
                    {
                        "account_id": cost.account_id.id,
                        "name": cost.name,
                        "credit": -amount if amount < 0 else 0,
                        "debit": amount if amount > 0 else 0,
                        "loan_extra_cost_id": cost.id,
                    }
                )
        return vals

    def _invoice_line_vals(self):
        vals = super()._invoice_line_vals()
        for cost in self.loan_id.extra_cost_ids.filtered(
            lambda c: c.payment_type == "periodic"
        ):
            amount = cost._compute_periodic_amount(self)
            if amount:
                vals.append(
                    {
                        "name": cost.name,
                        "quantity": 1,
                        "price_unit": amount,
                        "account_id": cost.account_id.id,
                        "loan_extra_cost_id": cost.id,
                    }
                )
        return vals
