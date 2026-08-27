# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_account_move_line_vals(self):
        vals_list = super()._get_account_move_line_vals()
        if self.repair_id:
            for vals in vals_list:
                vals["repair_order_id"] = self.repair_id.id
        return vals_list
