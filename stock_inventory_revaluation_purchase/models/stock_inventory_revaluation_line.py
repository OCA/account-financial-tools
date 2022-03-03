# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models


class StockInventoryRevaluationLine(models.Model):
    _inherit = "stock.inventory.revaluation.line"

    def _prepare_base_line(self, move, revaluation_line):
        res = super(StockInventoryRevaluationLine, self)._prepare_base_line(
            move, revaluation_line
        )
        res["purchase_line_id"] = revaluation_line.stock_move_id.purchase_line_id.id
        return res
