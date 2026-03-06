# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountLoan(models.Model):
    _inherit = "account.loan"
    advance_payment = fields.Boolean(
        default=False,
        help=(
            "If set to true, the start/end dates on the interests will be in the"
            "future compared to the date on the line"
        ),
        required=False,
    )
