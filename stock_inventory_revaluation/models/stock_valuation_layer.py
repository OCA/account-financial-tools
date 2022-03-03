# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockValuationLayer(models.Model):
    """Stock Valuation Layer"""

    _inherit = "stock.valuation.layer"

    stock_inventory_revaluation_line_id = fields.Many2one(
        "stock.inventory.revaluation.line", "Inventory revaluation line"
    )
