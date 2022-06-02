# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockInventoryRevaluation(models.Model):
    _inherit = "stock.inventory.revaluation"

    def _prepare_valuation_lines(
        self, move, original_value, price_subtotal, additional_value, bill_qty
    ):
        """In  case of dropship do not consider the layer out for the value"""
        res = super()._prepare_valuation_lines(
            move, original_value, price_subtotal, additional_value, bill_qty
        )
        if move._is_dropshipped():
            res["used_stock_valuation_layer_ids"] = [
                (
                    6,
                    0,
                    [
                        layer.id
                        for layer in move.stock_valuation_layer_ids.filtered(
                            lambda l: l.quantity > 0.0
                            and not l.stock_inventory_revaluation_line_id
                        )
                    ],
                )
            ]
        return res

    def _get_affected_qty(self, line, layers):
        """in case of dropship consider all quantity"""
        remaining_qty = super()._get_affected_qty(line, layers)
        if line.stock_move_id._is_dropshipped():
            remaining_qty = sum(layers.mapped("quantity"))
        return remaining_qty

    def _create_revaluation_layers(
        self, revaluation_to_add, linked_layer, revaluation, line
    ):
        """In case of dropship we create 2 new layers"""
        if line.stock_move_id._is_dropshipped():
            layer_vals = self._prepare_layer_vals(
                revaluation_to_add, linked_layer, revaluation, line
            )
            valuation_layer1 = self.env["stock.valuation.layer"].create(layer_vals)
            layer_vals = self._prepare_layer_vals(
                -revaluation_to_add, linked_layer, revaluation, line
            )
            valuation_layer2 = self.env["stock.valuation.layer"].create(layer_vals)
            line.created_stock_valuation_layer_ids = [
                (4, valuation_layer1.id),
                (4, valuation_layer2.id),
            ]
            # now, the values are calculated so we include the layer out as used_layer
            line.used_stock_valuation_layer_ids = [
                (4, svl.id)
                for svl in line.stock_move_id.stock_valuation_layer_ids.filtered(
                    lambda l: l.quantity < 0.0
                    and not l.stock_inventory_revaluation_line_id
                )
            ]
            return [valuation_layer1.id, valuation_layer2.id]
        else:
            return super()._create_revaluation_layers(
                revaluation_to_add, linked_layer, revaluation, line
            )
