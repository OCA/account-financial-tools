# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_repair_sale_lines(self):
        self.ensure_one()
        sale_lines = self.env["sale.order.line"].search(
            [
                ("move_ids", "in", self.id),
                (
                    "order_id",
                    "=",
                    self.repair_id.sale_order_id.id
                    if self.repair_id.sale_order_id
                    else False,
                ),
            ]
        )
        # filter by product
        sale_lines = sale_lines.filtered(
            lambda line: line.product_id == self.product_id
        )
        return sale_lines[0] if sale_lines else self.env["sale.order.line"]

    @api.model
    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, svl_id, description
    ):
        res = super()._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )
        repair = self.repair_id
        if repair:
            sale_line = self._get_repair_sale_lines()
            if not sale_line:
                return res
            for line in res:
                line[2]["sale_line_id"] = sale_line.id
        return res

    def _create_repair_sale_order_line(self):
        res = super()._create_repair_sale_order_line()
        for move in self:
            sale_lines = move._get_repair_sale_lines()
            move.account_move_ids.mapped("line_ids").write(
                {"sale_line_id": sale_lines.id}
            )
        return res
