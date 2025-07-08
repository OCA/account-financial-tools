# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    def _prepare_account_move_line_values(self):
        values = super()._prepare_account_move_line_values()
        values.update(
            {
                "stock_valuation_adjustment_line_id": self.id,
                "stock_landed_cost_id": self.cost_id.id,
            }
        )
        return values
