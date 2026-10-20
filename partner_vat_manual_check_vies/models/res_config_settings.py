# Copyright 2026 Le Filament (https://le-filament.com)
# License LGPL-3.0 (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vies_vat_api = fields.Selection(
        related="company_id.vies_vat_api",
        readonly=False,
    )
