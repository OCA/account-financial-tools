# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import models


class AccountLoanLine(models.Model):
    _inherit = "account.loan.line"

    def _get_start_end_dates(self, account_dict):
        loan_lines = self.loan_id.line_ids.sorted(lambda line: line.sequence)
        if not self.loan_id.advance_payment:
            if self == loan_lines[:1] and self.sequence == 1:
                account_dict["start_date"] = self.loan_id.start_date
                account_dict["end_date"] = self.date
            else:
                account_dict["start_date"] = (
                    self.date
                    - relativedelta(months=self.loan_id.method_period)
                    + relativedelta(days=1)
                )
                account_dict["end_date"] = self.date
        else:
            if self != loan_lines[-1:]:
                account_dict["start_date"] = self.date
                account_dict["end_date"] = (
                    self.date
                    + relativedelta(months=self.loan_id.method_period)
                    - relativedelta(days=1)
                )
            else:
                account_dict["start_date"] = None
                account_dict["end_date"] = None

    def _add_start_end_dates_information(self, vals):
        interest_expenses_account_id = self.loan_id.interest_expenses_account_id.id
        interests_dict = next(
            (
                item
                for item in vals
                if item["account_id"] == interest_expenses_account_id
            ),
            None,
        )
        if interests_dict:
            self._get_start_end_dates(interests_dict)

    def _add_interests_values(self, vals):
        self.ensure_one()
        vals = super()._add_interests_values(vals)
        self._add_start_end_dates_information(vals)
        return vals

    def _add_interests_values_invoice_line(self, vals):
        self.ensure_one()
        vals = super()._add_interests_values_invoice_line(vals)
        self._add_start_end_dates_information(vals)
        return vals
