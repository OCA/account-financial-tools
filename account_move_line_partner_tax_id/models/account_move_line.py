# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partner_vat = fields.Char(
        string="Partner Tax ID",
        related="partner_id.vat",
        store=True,
    )
