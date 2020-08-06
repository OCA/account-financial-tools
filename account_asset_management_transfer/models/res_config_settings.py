# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    asset_transfer_settings = fields.Boolean(
        related="company_id.asset_transfer_settings", readonly=False
    )
    asset_transfer_journal_id = fields.Many2one(
        related="company_id.asset_transfer_journal_id", readonly=False
    )
