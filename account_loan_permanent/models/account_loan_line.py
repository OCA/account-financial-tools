# Copyright 2024 Som IT Cooperatiu SCCL - Nicolás Ramos <nicolas.ramos@somit.coop>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import api, models


class AccountLoanLine(models.Model):
    """Extend account.loan.line model for permanent loan lines."""

    _inherit = "account.loan.line"

    def _generate_move(self, journal=False, account=False):
        """Generate move for permanent loan lines."""
        res = super()._generate_move(journal=journal, account=account)
        for line in self:
            if line.loan_id.is_permanent:
                line._ensure_min_periods()
        return res

    def _ensure_min_periods(self):
        """Ensure minimum periods for permanent loans."""
        self.ensure_one()
        last_line = self.loan_id.line_ids.sorted(key=lambda r: r.sequence)[-1]
        future_periods = self.loan_id.periods - self.sequence
        if future_periods < self.loan_id.min_periods:
            new_line = self._create_next_line(last_line)
            self.loan_id.periods += 1
            new_line._check_amount()

    @api.model
    def _create_next_line(self, last_line):
        """Create the next line for a permanent loan."""
        new_sequence = last_line.sequence + 1
        new_date = last_line.date + relativedelta(months=1)

        new_line_vals = {
            "loan_id": last_line.loan_id.id,
            "sequence": new_sequence,
            "date": new_date,
            "rate": last_line.rate,
            "pending_principal_amount": last_line.loan_id.loan_amount,
            "long_term_pending_principal_amount": last_line.loan_id.loan_amount,
        }

        new_line = self.create(new_line_vals)
        new_line._check_amount()

        return new_line

    @api.depends("loan_id.rate_period", "pending_principal_amount")
    def _compute_interests(self):
        """Compute interests for permanent loan lines."""
        for record in self:
            if record.loan_id.is_permanent and record.loan_id.loan_type == "interest":
                record.interests_amount = (
                    record.pending_principal_amount * record.loan_id.rate_period / 100
                )
            else:
                return super(AccountLoanLine, record)._compute_interests()
        return True

    def _compute_amount(self):
        """Compute amount for permanent loan lines."""
        for record in self:
            if record.loan_id.is_permanent and record.loan_id.loan_type == "interest":
                record._compute_interests()
                record.payment_amount = record.interests_amount
                record.principal_amount = 0
                record.pending_principal_amount = record.loan_id.loan_amount
                record.final_pending_principal_amount = record.loan_id.loan_amount
            else:
                return super(AccountLoanLine, record)._compute_amount()
        return True

    def _check_amount(self):
        """Check and adjust amounts for permanent loan lines."""
        for record in self:
            if record.loan_id.is_permanent and record.loan_id.loan_type == "interest":
                record._compute_interests()
                record.payment_amount = record.interests_amount
                record.principal_amount = 0
                record.pending_principal_amount = record.loan_id.loan_amount
                record.final_pending_principal_amount = record.loan_id.loan_amount
            else:
                return super(AccountLoanLine, record)._check_amount()
        return True
