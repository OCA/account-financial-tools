# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    stock_valuation_adjustment_line_id = fields.Many2one(
        comodel_name="stock.valuation.adjustment.lines",
        string="Stock Valuation Adjustment Line",
        store=True,
        index=True,
    )
    stock_landed_cost_id = fields.Many2one(
        "stock.landed.cost",
        related="stock_valuation_adjustment_line_id.cost_id",
        store=True,
    )
