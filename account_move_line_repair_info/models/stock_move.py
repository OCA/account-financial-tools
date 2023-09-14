# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _create_account_move_line(
        self,
        credit_account_id,
        debit_account_id,
        journal_id,
        qty,
        description,
        svl_id,
        cost,
    ):
        am_model = self.env["account.move"]
        res = super()._create_account_move_line(
            credit_account_id,
            debit_account_id,
            journal_id,
            qty,
            description,
            svl_id,
            cost,
        )
        if self.repair_id:
            current_move = am_model.search([("stock_move_id", "=", self.id)])
            if current_move:
                current_move.line_ids.write(
                    {
                        "repair_order_id": self.repair_id.id,
                    }
                )
        return res
