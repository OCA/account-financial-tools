# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountLoanPost(models.TransientModel):
    _inherit = "account.loan.post"

    def move_line_vals(self):
        res = super().move_line_vals()
        partner = self.loan_id.partner_id.with_company(self.loan_id.company_id)
        for cost in self.loan_id.extra_cost_ids.filtered(
            lambda c: c.payment_type == "upfront" and c.amount
        ):
            res.append(
                {
                    "account_id": cost.account_id.id,
                    "name": cost.name,
                    "partner_id": partner.id,
                    "debit": cost.amount if cost.amount > 0 else 0,
                    "credit": -cost.amount if cost.amount < 0 else 0,
                }
            )
            res.append(
                {
                    "account_id": self.account_id.id,
                    "name": cost.name,
                    "partner_id": partner.id,
                    "credit": cost.amount if cost.amount > 0 else 0,
                    "debit": -cost.amount if cost.amount < 0 else 0,
                }
            )
        return res
