# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockValuationLayer(models.Model):

    _inherit = "stock.valuation.layer"

    def _validate_accounting_entries(self):
        res = super()._validate_accounting_entries()
        for svl in self:
            if svl.stock_move_id.repair_id:
                current_move = svl.account_move_id
                if current_move:
                    current_move.line_ids.write(
                        {
                            "repair_order_id": svl.stock_move_id.repair_id.id,
                        }
                    )
        return res
