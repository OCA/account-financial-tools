# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    stock_inventory_revaluation_line_id = fields.Many2one(
        "stock.inventory.revaluation.line"
    )
