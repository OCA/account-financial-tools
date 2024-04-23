# Copyright 2024 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    asset_move_auto_validate = fields.Boolean(
        default=True,
        help="Determine if the new account move should be automatically posted",
    )
