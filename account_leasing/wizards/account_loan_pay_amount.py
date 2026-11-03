# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.exceptions import UserError


class AccountLoan(models.TransientModel):
    _inherit = "account.loan.pay.amount"
    _description = "Loan pay amount"

    def _pre_loan_pay_cheks(self):
        if self.loan_id.loan_type == "leasing":
            if self.loan_id.line_ids.filtered(
                lambda r: r.date <= self.date and not r.move_ids
            ):
                raise UserError(self.env._("Some invoices are not created"))
            if self.loan_id.line_ids.filtered(
                lambda r: r.date > self.date and r.move_ids
            ):
                raise UserError(self.env._("Some future invoices already exists"))
            return
        return super()._pre_loan_pay_cheks()
