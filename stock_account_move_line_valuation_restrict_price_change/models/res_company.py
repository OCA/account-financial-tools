# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    restrict_account_move_line_change_after_valuation = fields.Boolean(
        help="Check this to restrict the account entries price change after"
        "stock valuations generation."
    )
