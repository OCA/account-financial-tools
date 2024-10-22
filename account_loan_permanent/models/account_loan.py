# Copyright 2024 Som IT Cooperatiu SCCL - Nicolás Ramos <nicolas.ramos@somit.coop>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class AccountLoan(models.Model):
    """Extend account.loan model to add permanent loan functionality."""

    _inherit = "account.loan"

    is_permanent = fields.Boolean(
        default=False,
        help="If checked, this loan will be treated as a permanent loan. "
        "Permanent loans are only allowed for 'Only interest' type loans "
        "and will continue generating new periods indefinitely.",
    )
    min_periods = fields.Integer(
        string="Minimum Periods",
        default=60,
        help="The minimum number of periods for a permanent loan. "
        "This ensures that the loan will have at least this many periods "
        "before potentially generating new ones.",
    )

    @api.onchange("is_permanent", "loan_type")
    def _onchange_is_permanent(self):
        """Handle changes in is_permanent and loan_type fields."""
        if self.is_permanent and self.loan_type != "interest":
            self.is_permanent = False
            return {
                "warning": {
                    "title": _("Invalid Loan Type"),
                    "message": _("Permanent loans can only be of type 'Only interest'"),
                }
            }
        if self.is_permanent:
            self.residual_amount = 0
            self.periods = max(self.periods, self.min_periods)

    def _create(self, data_list):
        res = super()._create(data_list)
        for loan in res.filtered(lambda l: l.is_permanent):
            loan.periods = loan.min_periods
        return res

    @api.model
    def _generate_loan_entries(self, date):
        """
        Generate the moves of unfinished loans before date
        :param date:
        :return:
        """
        res = super()._generate_loan_entries(date)
        for loan in self.filtered(lambda l: l.is_permanent):
            lines = loan.line_ids.filtered(lambda l: l.date <= date and not l.move_ids)
            if lines:
                res += lines._generate_move()
                loan.periods += len(lines)
                last_line = loan.line_ids.sorted(key=lambda r: r.sequence)[-1]
                while last_line.date <= date:
                    new_line = self.env["account.loan.line"]._create_next_line(
                        last_line
                    )
                    last_line = new_line
                    loan.periods += 1
        return res
