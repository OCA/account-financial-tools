# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_move_stock_valuation_layer_ids(self, move):
        """In  case of dropship do not consider the layer out for the value"""
        layers = super()._get_move_stock_valuation_layer_ids(move)
        if move._is_dropshipped():
            return layers.filtered(
                lambda l: l.quantity > 0.0 and not l.stock_inventory_revaluation_line_id
            )
        return layers
