# Copyright 2021 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partner_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Partner's Country",
        related="partner_id.country_id",
        store=True,
    )
