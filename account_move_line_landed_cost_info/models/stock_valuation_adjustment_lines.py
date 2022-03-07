# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    def _create_account_move_line(
        self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id
    ):
        """
        Adds the adjustment line to the account move line. This method is called always
        for a single line in self.
        """
        res = super()._create_account_move_line(
            move, credit_account_id, debit_account_id, qty_out, already_out_account_id
        )
        for line in res:
            if isinstance(line, list) and isinstance(line[2], dict):
                line[2]["stock_valuation_adjustment_line_id"] = self.id
                line[2]["stock_landed_cost_id"] = self.cost_id.id
        return res
