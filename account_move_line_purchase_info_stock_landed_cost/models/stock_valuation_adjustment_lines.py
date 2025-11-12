from odoo import models


class AdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    def _create_accounting_entries(self, move, qty_out):
        res = super()._create_accounting_entries(move, qty_out)
        for entry in res:
            values = entry[2]
            purchase_line = self.move_id.purchase_line_id
            if purchase_line:
                values["oca_purchase_line_id"] = purchase_line.id
        return res
