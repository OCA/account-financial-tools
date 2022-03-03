# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    stock_revaluation_count = fields.Integer(compute="_compute_stock_revaluation_count")
    show_create_stock_revaluation_button = fields.Boolean(
        compute="_compute_show_create_stock_revaluation_button"
    )

    def button_revaluate(self):
        """Create a revaluation record associated to this bill"""
        self.ensure_one()
        inventory_revaluation = self.env["stock.inventory.revaluation"].create(
            {
                "vendor_bill_id": self.id,
            }
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_inventory_revaluation.action_stock_inventory_revaluation"
        )
        return dict(
            action,
            view_mode="form",
            res_id=inventory_revaluation.id,
            views=[(False, "form")],
        )

    def action_view_inventory_revaluation_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_inventory_revaluation.action_stock_inventory_revaluation"
        )
        revaluations = self.env["stock.inventory.revaluation"].search(
            [("vendor_bill_id", "=", self.id)]
        )
        domain = [("id", "in", revaluations.ids)]
        context = dict(self.env.context, default_vendor_bill_id=self.id)
        views = [
            (
                self.env.ref(
                    "stock_inventory_revaluation.view_stock_inventory_revaluation_tree"
                ).id,
                "tree",
            ),
            (False, "form"),
        ]
        return dict(action, domain=domain, context=context, views=views)

    def _get_account_move_line_price_unit(self, currency, product_id):
        """get the price unit and qty of the move lines for a given product"""
        self.ensure_one()
        return sum(
            [
                currency._convert(
                    invl.price_subtotal,
                    invl.company_currency_id,
                    invl.company_id,
                    invl.move_id.date,
                )
                for invl in self.line_ids.filtered(lambda l: l.product_id == product_id)
            ]
        ), sum(
            [
                invl.quantity
                for invl in self.line_ids.filtered(lambda l: l.product_id == product_id)
            ]
        )

    def _compute_stock_revaluation_count(self):
        for rec in self:
            rec.stock_revaluation_count = self.env[
                "stock.inventory.revaluation"
            ].search_count([("vendor_bill_id", "=", rec.id)])

    def _compute_show_create_stock_revaluation_button(self):
        """By Default We show the create revaluation button always, to be inherited
        for other modules to change this behavior"""
        for rec in self:
            rec.show_create_stock_revaluation_button = True

    def _get_additional_value(self, move):
        """Get the additional value added to a stock move"""
        self.ensure_one()
        layers = self._get_move_stock_valuation_layer_ids(move)
        if self.move_type == "in_refund":
            # only in case of refund we consider previous revaluations
            original_value = sum(move.stock_valuation_layer_ids.mapped("value"))
        else:
            original_value = sum(layers.mapped("value"))
        price, bill_qty = self._get_account_move_line_price_unit(
            self.currency_id, move.product_id
        )
        if not bill_qty:
            # Cannot revaluate bill with 0 qty
            return original_value, original_value, 0.0
        move_qty = move.product_uom_qty
        qty_diff = move_qty - bill_qty
        if not bill_qty or not move_qty:
            # avoid ZeroDivisionError
            return original_value, price, 0.0, bill_qty
        new_price = price / bill_qty
        old_price = original_value / move_qty
        if abs(new_price) == abs(old_price):
            # If no price difference then there is no revaluation to do
            return original_value, price, 0.0, bill_qty
        if self.move_type == "in_refund":
            # WARNING: this is a corner case, when the price in the original invoice
            # the normal procedure is doing a full refund for the same price
            # and then a new vendor bill to revaluate, but it may happen to do a
            # refund just for adjusting the price.
            # Also, if the refund is for a return to supplier and the refund is
            # for a different price, this will apply as well
            additional_value = new_price * bill_qty
            # if abs(original_value) > new_price:
            price = -price
            additional_value = -additional_value
        else:
            # old value + new value - original value (in the layer) = additional value
            additional_value = (
                (old_price * qty_diff) + (new_price * bill_qty) - original_value
            )
        return original_value, price, additional_value, bill_qty

    def _get_move_stock_valuation_layer_ids(self, move):
        """Override this to exclude or add layers on different processes"""
        return move.stock_valuation_layer_ids.filtered(
            lambda l: not l.stock_inventory_revaluation_line_id
        )
