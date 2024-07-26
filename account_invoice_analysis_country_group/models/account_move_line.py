# Copyright 2024 ForgeFlow SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    country_group_id = fields.Many2one(
        compute="_compute_country_group_id",
        comodel_name="res.country.group",
        store=True,
        index=True,
    )

    @api.depends("partner_id")
    def _compute_country_group_id(self):
        for rec in self:
            rec.country_group_id = rec.partner_id.country_id.country_group_ids[0]
