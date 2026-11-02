# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extended configuration settings for payment accounts."""

    _inherit = "res.config.settings"

    inbound_payment_account_id = fields.Many2one(
        related="company_id.inbound_payment_account_id", readonly=False
    )
    outbound_payment_account_id = fields.Many2one(
        related="company_id.outbound_payment_account_id", readonly=False
    )
