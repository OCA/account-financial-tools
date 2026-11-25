# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountLoanPayAmount(models.TransientModel):
    _inherit = "account.loan.pay.amount"

    def new_line_vals(self, sequence):
        vals = super().new_line_vals(sequence)
        vals["is_manual_payment"] = True
        return vals
