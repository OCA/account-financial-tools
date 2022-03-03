# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockInventoryRevaluation(models.Model):
    _inherit = "stock.inventory.revaluation"

    def compute_inventory_revaluation(self):
        for revaluation in self:
            all_val_line_values = revaluation.get_valuation_lines()
            for val_line_values in all_val_line_values:
                self.env["stock.inventory.revaluation.line"].create(val_line_values)

    def _get_targeted_move_ids(self):
        """Gets the stock moves from the PO"""
        super(StockInventoryRevaluation, self)._get_targeted_move_ids()
        polines = self.vendor_bill_id.line_ids.mapped("purchase_line_id")
        stock_moves = self.env["stock.move"].search(
            [("purchase_line_id", "in", polines.ids)]
        )
        return stock_moves
