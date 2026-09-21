# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountLoan(models.Model):
    _inherit = "account.loan"

    extra_cost_ids = fields.One2many(
        "account.loan.extra.cost",
        "loan_id",
        string="Extra Costs",
        help="Insurance premiums, fees and any other recurring or upfront "
        "costs associated with this loan.",
    )

    @api.depends("line_ids.extra_cost_amount")
    def _compute_total_amounts(self):
        res = super()._compute_total_amounts()
        for record in self:
            lines = record.line_ids.filtered(lambda r: r.move_ids)
            extra_cost = sum(lines.mapped("extra_cost_amount")) or 0.0
            record.pending_principal_amount += extra_cost
        return res

    def _compute_draft_lines(self):
        res = super()._compute_draft_lines()
        for record in self:
            amount = record.loan_amount
            for line in record.line_ids.sorted("sequence"):
                line.pending_principal_amount = amount
                line._check_amount()
                amount -= (
                    line.payment_amount - line.interests_amount - line.extra_cost_amount
                )
            if record.long_term_loan_account_id:
                record._check_long_term_principal_amount()
        return res

    def _compute_posted_lines(self):
        amount = self.loan_amount
        for line in self.line_ids.sorted("sequence"):
            if line.move_ids:
                amount = line.final_pending_principal_amount
            else:
                line.rate = self.rate_period
                line.pending_principal_amount = amount
                line._check_amount()
                amount -= (
                    line.payment_amount - line.interests_amount - line.extra_cost_amount
                )
        if self.long_term_loan_account_id:
            self._check_long_term_principal_amount()
