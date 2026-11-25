# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    lock_date = fields.Date(
        tracking=True,
        help="Lock account entries before this date (included)",
    )
