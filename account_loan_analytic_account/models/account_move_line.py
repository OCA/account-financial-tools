# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    loan_id = fields.Many2one(
        related="move_id.loan_id",
        store=True,
    )

    @api.depends("loan_id", "loan_id.analytic_distribution")
    def _compute_analytic_distribution(self):
        res = super()._compute_analytic_distribution()
        for rec in self:
            if rec.loan_id and rec.loan_id.analytic_distribution:
                if rec.account_id.id == rec.loan_id.interest_expenses_account_id.id:
                    rec.analytic_distribution = rec.loan_id.analytic_distribution
        return res
