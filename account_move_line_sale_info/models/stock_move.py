# Copyright 2020-23 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_account_move_line_vals(self):
        res = super()._get_account_move_line_vals()
        res[0]["sale_line_id"] = self.sale_line_id.id
        return res
