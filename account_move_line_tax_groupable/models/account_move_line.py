# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    taxes_applied = fields.Char(
        string="Taxes Applied (combined)",
        compute="_compute_taxes_applied",
        store=True,
        index=True,
    )

    @api.multi
    @api.depends("tax_ids.name")
    def _compute_taxes_applied(self):
        for line in self:
            line.taxes_applied = "; ".join(line.tax_ids.mapped("name"))
