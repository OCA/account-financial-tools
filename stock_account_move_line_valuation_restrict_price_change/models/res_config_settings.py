# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    restrict_account_move_line_change_after_valuation = fields.Boolean(
        related="company_id.restrict_account_move_line_change_after_valuation",
        readonly=False,
    )
