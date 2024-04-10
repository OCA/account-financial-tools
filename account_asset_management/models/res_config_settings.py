# Copyright 2024 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    asset_move_auto_validate = fields.Boolean(
        help="Determine if the new account move should be automatically posted",
        related="company_id.asset_move_auto_validate",
        readonly=False,
    )
