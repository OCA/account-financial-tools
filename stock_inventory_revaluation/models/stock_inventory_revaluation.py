# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class StockInventoryRevaluation(models.Model):
    _name = "stock.inventory.revaluation"
    _description = "Stock Inventory Revaluation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_account_journal_id(self):
        return self.env["ir.property"]._get(
            "property_stock_journal", "product.category"
        )

    name = fields.Char(
        "Name", default=lambda self: _("New"), copy=False, readonly=True, tracking=True
    )
    add_from_stock_move = fields.Many2one("stock.move", "Add From Stock Move")
    date = fields.Date(
        "Date",
        default=fields.Date.context_today,
        copy=False,
        required=True,
        states={"done": [("readonly", True)]},
        tracking=True,
    )
    stock_inventory_revaluation_line_ids = fields.One2many(
        "stock.inventory.revaluation.line",
        "stock_inventory_revaluation_id",
        "Revaluation Lines",
        copy=True,
        states={"done": [("readonly", True)]},
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Posted"), ("cancel", "Cancelled")],
        "State",
        default="draft",
        copy=False,
        readonly=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", related="vendor_bill_id.company_id"
    )

    vendor_bill_id = fields.Many2one(
        "account.move",
        string="Vendor Bill",
        help="Vendor Bill that triggers the revaluation",
        copy=False,
        domain=[("move_type", "=", "in_invoice")],
    )
    account_move_id = fields.Many2one(
        "account.move", string="Revaluation entry", readonly=True, copy=False
    )
    currency_id = fields.Many2one("res.currency", related="vendor_bill_id.currency_id")

    @api.onchange("add_from_stock_move")
    def onchange_add_from_stock_move(self):
        if self.add_from_stock_move:
            val_line_values = self.get_valuation_lines(self.add_from_stock_move)
            for vals in val_line_values:
                self.env["stock.inventory.revaluation.line"].create(vals)
            self.add_from_stock_move = False

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "stock.inventory.revaluation"
            )
        return super().create(vals)

    def unlink(self):
        self.button_cancel()
        return super().unlink()

    def button_cancel(self):
        if any(revaluation.state == "done" for revaluation in self):
            raise UserError(
                _(
                    "Validated revaluation cannot be cancelled, but you could do "
                    "another revaluation"
                )
            )
        return self.write({"state": "cancel"})

    def button_validate(self):
        for revaluation in self:
            revaluation = revaluation.with_company(revaluation.company_id)
            move = self.env["account.move"]
            move_vals = self._prepare_move_vals(revaluation)
            valuation_layer_ids = []
            revaluation_to_add_byproduct = defaultdict(lambda: 0.0)
            for line in revaluation.stock_inventory_revaluation_line_ids.filtered(
                lambda l: l.additional_value
            ):
                layers = self.vendor_bill_id._get_move_stock_valuation_layer_ids(
                    line.stock_move_id
                )
                remaining_qty = self._get_remaining_qty(line, layers)
                linked_layer = layers[:1]
                # Prorate the value at what's still in stock
                revaluation_to_add = (
                    remaining_qty / line.stock_move_id.product_qty
                ) * line.additional_value
                if not revaluation.company_id.currency_id.is_zero(revaluation_to_add):
                    new_layer_ids = self._create_revaluation_layers(
                        revaluation_to_add, linked_layer, revaluation, line
                    )
                    valuation_layer_ids.extend(new_layer_ids)

                # Update the AVCO
                product = line.product_id
                if product.cost_method == "average":
                    revaluation_to_add_byproduct[product] += revaluation_to_add
                # Products with manual inventory valuation are ignored because they
                # do not need to create journal entries.
                if product.valuation != "real_time":
                    continue
                # `remaining_qty` is negative if the move is out and delivered proudcts
                #  that were not
                # in stock._get_qty_out
                qty_out = self._get_qty_out(line, remaining_qty)
                move_vals["line_ids"] += line._create_accounting_entries(
                    move, line, qty_out
                )

            # batch standard price computation avoid recompute quantity_svl at
            # each iteration
            products = self.env["product.product"].browse(
                p.id for p in revaluation_to_add_byproduct.keys()
            )
            for (
                product
            ) in products:  # iterate on recordset to prefetch efficiently quantity_svl
                if not float_is_zero(
                    product.quantity_svl, precision_rounding=product.uom_id.rounding
                ):
                    product.with_company(revaluation.company_id).sudo().with_context(
                        disable_auto_svl=True
                    ).standard_price += (
                        revaluation_to_add_byproduct[product] / product.quantity_svl
                    )

            move_vals["stock_valuation_layer_ids"] = [(6, None, valuation_layer_ids)]
            # We will only create the accounting entry when there are defined lines
            # (the lines will be those linked to products of real_time valuation
            # category).
            revaluation_vals = {"state": "done"}
            if move_vals.get("line_ids"):
                move = move.create(move_vals)
                revaluation_vals.update({"account_move_id": move.id})
            revaluation.write(revaluation_vals)
            if revaluation.account_move_id:
                move._post()

            if (
                revaluation.vendor_bill_id
                and revaluation.vendor_bill_id.state == "posted"
                and revaluation.company_id.anglo_saxon_accounting
            ):
                all_amls = (
                    revaluation.vendor_bill_id.line_ids
                    | revaluation.account_move_id.line_ids
                )
                for product in revaluation.stock_inventory_revaluation_line_ids.mapped(
                    "product_id"
                ):
                    accounts = product.product_tmpl_id.get_product_accounts()
                    input_account = accounts["stock_input"]
                    # re-reconcile interim accounts
                    all_amls.filtered(
                        lambda aml: aml.account_id == input_account
                        and aml.product_id == product
                        and not aml.full_reconcile_id
                    ).remove_move_reconcile()
                    all_amls.filtered(
                        lambda aml: aml.account_id == input_account
                        and aml.product_id == product
                        and not aml.full_reconcile_id
                    ).reconcile()
        return True

    def get_valuation_lines(self, move=False):
        self.ensure_one()
        lines = []
        moves = move or self._get_targeted_move_ids()
        for move in moves:
            # it doesn't make sense to make a revaluation for a product that
            # isn't set as being valuated in real time at real revaluation
            if (
                move.product_id.cost_method not in ("fifo", "average")
                or move.state == "cancel"
                or not move.product_qty
            ):
                continue
            (
                original_value,
                price_subtotal,
                additional_value,
                bill_qty,
            ) = self.vendor_bill_id._get_additional_value(move)
            vals = self._prepare_valuation_lines(
                move, original_value, price_subtotal, additional_value, bill_qty
            )
            lines.append(vals)
        return lines

    def action_view_stock_valuation_layers(self):
        self.ensure_one()
        stock_valuation_layers = self.mapped(
            "stock_inventory_revaluation_line_ids.used_stock_valuation_layer_ids"
        ) + self.mapped(
            "stock_inventory_revaluation_line_ids.created_stock_valuation_layer_ids"
        )
        domain = [("id", "in", stock_valuation_layers.ids)]
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_account.stock_valuation_layer_action"
        )
        return dict(action, domain=domain)

    def _get_targeted_move_ids(self):
        return self.stock_inventory_revaluation_line_ids.mapped("stock_move_id")

    def _prepare_move_vals(self, revaluation):
        journal = self._get_journal(revaluation)
        vals = {
            "journal_id": journal.id,
            "date": revaluation.date,
            "ref": revaluation.name,
            "line_ids": [],
            "move_type": "entry",
        }
        return vals

    def _prepare_layer_vals(self, revaluation_to_add, linked_layer, revaluation, line):
        return {
            "value": revaluation_to_add,
            "quantity": 0,
            "remaining_qty": 0,
            "stock_valuation_layer_id": linked_layer.id,
            "description": revaluation.name,
            "stock_move_id": line.stock_move_id.id,
            "product_id": line.product_id.id,
            # The layer is linked to the revaluation line
            "stock_inventory_revaluation_line_id": line.id,
            "company_id": revaluation.company_id.id,
        }

    def _prepare_valuation_lines(
        self, move, original_value, price_subtotal, additional_value, bill_qty
    ):
        vals = {
            "name": self.name + " " + move.product_id.display_name,
            "product_id": move.product_id.id,
            "stock_move_id": move.id,
            "quantity": bill_qty,
            "stock_inventory_revaluation_id": self.id,
            "used_stock_valuation_layer_ids": [
                (4, layer.id) for layer in move.stock_valuation_layer_ids
            ],
            "original_value": original_value,
            "price_subtotal": price_subtotal,
            "additional_value": additional_value,
        }
        return vals

    def _get_remaining_qty(self, line, layers):
        """returns the remaining qty for a revalaution line"""
        remaining_qty = sum(layers.mapped("remaining_qty"))
        if line.stock_move_id._is_out():
            remaining_qty = -1 * sum(layers.mapped("quantity"))
        return remaining_qty

    def _create_revaluation_layers(
        self, revaluation_to_add, linked_layer, revaluation, line
    ):
        """Creates layer for the revaluation"""
        layer_vals = self._prepare_layer_vals(
            revaluation_to_add, linked_layer, revaluation, line
        )
        valuation_layer = self.env["stock.valuation.layer"].create(layer_vals)
        line.created_stock_valuation_layer_ids = [(4, valuation_layer.id)]
        linked_layer.remaining_value += revaluation_to_add
        return [valuation_layer.id]

    def _get_qty_out(self, line, remaining_qty):
        qty_out = 0
        if line.stock_move_id._is_in():
            qty_out = line.stock_move_id.product_qty - remaining_qty
        elif line.stock_move_id._is_out():
            qty_out = line.stock_move_id.product_qty
        return qty_out

    def _get_journal(self, revaluation):
        journal = (
            self._default_account_journal_id() or revaluation.vendor_bill_id.journal_id
        )
        return journal
