from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    fiscalyear_last_day = fields.Integer(
        related="company_id.fiscalyear_last_day", readonly=False
    )
    fiscalyear_last_month = fields.Selection(
        related="company_id.fiscalyear_last_month", readonly=False
    )
