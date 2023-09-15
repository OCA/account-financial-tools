# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountLoanGenerateWizard(models.TransientModel):
    _name = "account.loan.generate.wizard"
    _description = "Loan generate wizard"

    date = fields.Date(
        "Account Date",
        required=True,
        help="Choose the period for which you want to automatically post the "
        "depreciation lines of running assets",
        default=fields.Date.context_today,
    )
    loan_type = fields.Selection(
        [("leasing", "Leasings"), ("loan", "Loans")], required=True, default="loan"
    )

    def _run_leasing(self):
        created_ids = self.env["account.loan"]._generate_leasing_entries(self.date)
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(created_ids) == 0:
            return
        result["domain"] = [("id", "in", created_ids)]
        return result

    def _run_loan(self):
        created_ids = self.env["account.loan"]._generate_loan_entries(self.date)
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_line_form"
        )
        if len(created_ids) == 0:
            return
        result["domain"] = [("id", "in", created_ids)]
        return result

    def run(self):
        self.ensure_one()
        if self.loan_type == "leasing":
            return self._run_leasing()
        return self._run_loan()
