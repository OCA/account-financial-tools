# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    loan_extra_cost_id = fields.Many2one(
        "account.loan.extra.cost",
        readonly=True,
        ondelete="restrict",
        help="Set on journal lines created for a periodic extra cost of a "
        "loan installment. Used to reconcile amounts back to the loan line "
        "regardless of the account chosen.",
    )
