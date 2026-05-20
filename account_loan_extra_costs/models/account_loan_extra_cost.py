# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountLoanExtraCost(models.Model):
    _name = "account.loan.extra.cost"
    _description = "Loan Extra Cost (Insurance, Fee...)"

    loan_id = fields.Many2one(
        "account.loan",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(required=True, string="Description")
    company_id = fields.Many2one(
        "res.company",
        related="loan_id.company_id",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="loan_id.currency_id",
    )
    payment_type = fields.Selection(
        [
            ("upfront", "Upfront (at posting)"),
            ("periodic", "Periodic (each installment)"),
        ],
        required=True,
        default="periodic",
    )
    calculation_method = fields.Selection(
        [
            ("fixed", "Fixed Amount"),
            ("rate_initial_capital", "Rate on Initial Capital"),
            ("rate_remaining_per_period", "Rate on Remaining Capital (per period)"),
            (
                "rate_remaining_annual",
                "Rate on Remaining Capital (annual, at anniversary)",
            ),
        ],
        required=True,
        default="fixed",
    )
    amount = fields.Monetary(
        currency_field="currency_id",
        help="Fixed amount per installment "
        "(or upfront amount if payment type is Upfront).",
    )
    rate = fields.Float(
        digits=(8, 6),
        string="Annual Rate (%)",
        help="Annual rate applied to capital according to the calculation method.",
    )
    account_id = fields.Many2one(
        "account.account",
        required=True,
        string="Expense Account",
        domain="[('company_ids', '=', company_id), ('deprecated', '=', False)]",
    )

    def _compute_periodic_amount(self, line):
        self.ensure_one()
        if self.payment_type == "upfront":
            return 0.0

        loan = line.loan_id
        periods_per_year = 12.0 / loan.method_period

        if self.calculation_method == "fixed":
            return self.amount

        elif self.calculation_method == "rate_initial_capital":
            return loan.currency_id.round(
                loan.loan_amount * self.rate / 100.0 / periods_per_year
            )

        elif self.calculation_method == "rate_remaining_per_period":
            return loan.currency_id.round(
                line.pending_principal_amount * self.rate / 100.0 / periods_per_year
            )

        elif self.calculation_method == "rate_remaining_annual":
            periods_per_year_int = int(round(periods_per_year))
            year_number = (line.sequence - 1) // periods_per_year_int
            anniversary_sequence = year_number * periods_per_year_int + 1
            anniversary_line = loan.line_ids.filtered(
                lambda r: r.sequence == anniversary_sequence
            )
            capital = (
                anniversary_line.pending_principal_amount
                if anniversary_line
                else line.pending_principal_amount
            )
            return loan.currency_id.round(
                capital * self.rate / 100.0 / periods_per_year
            )

        return 0.0
