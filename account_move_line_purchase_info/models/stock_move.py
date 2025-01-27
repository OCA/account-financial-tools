# Copyright 2019 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, svl_id, description
    ):
        res = super()._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )
        for line in res:
            line[2]["oca_purchase_line_id"] = self.purchase_line_id.id
        return res
