from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    revaluation_auto_created = fields.Boolean(
        related="company_id.revaluation_auto_created", readonly=False
    )
