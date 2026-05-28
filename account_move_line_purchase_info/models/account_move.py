# Copyright 2019 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_in_lines_vals(self):
        res = super()._stock_account_prepare_anglo_saxon_in_lines_vals()
        # Cases in which we have multiple invoice lines with same product
        # and quantity. We want to ensure that each purchase.order.line is
        # only assigned to two distinct price-difference pairs of the same
        # invoice.
        assigned_pols_per_move = {}
        # Core emits two consecutive dicts per eligible invoice line
        # (price-diff + stock-input correction) sharing move_id, product_id
        # and quantity. pair_pending carries the POL chosen for the first
        # dict over to the second one so both halves of the pair are linked
        # to the same purchase.order.line. It is popped as soon as reused.
        pair_pending = {}
        for i, vals in enumerate(res):
            move_id = vals["move_id"]
            key = (move_id, vals["product_id"], vals["quantity"])
            if key in pair_pending:
                res[i]["oca_purchase_line_id"] = pair_pending.pop(key)
                continue
            assigned = assigned_pols_per_move.setdefault(move_id, set())
            am = self.env["account.move"].browse(move_id)
            candidate_pols = am.invoice_line_ids.filtered(
                lambda il: il.product_id.id == vals["product_id"]
                and il.quantity == vals["quantity"]
            ).mapped("purchase_line_id")
            available = candidate_pols.filtered(lambda pol: pol.id not in assigned)
            if available:
                chosen_id = available[0].id
                assigned.add(chosen_id)
                res[i]["oca_purchase_line_id"] = chosen_id
                pair_pending[key] = chosen_id
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Set related None, to make it compute and avoid base related to purchase_line_id
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        related=None,
        store=True,
        index=True,
        compute="_compute_purchase_id",
    )

    oca_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="OCA Purchase Line",
        store=True,
        index=True,
        compute="_compute_oca_purchase_line_id",
    )

    @api.depends("purchase_line_id")
    def _compute_oca_purchase_line_id(self):
        for rec in self:
            if rec.purchase_line_id:
                rec.oca_purchase_line_id = rec.purchase_line_id

    def _prepare_pdiff_aml_vals(self, qty, unit_valuation_difference):
        vals_list = super()._prepare_pdiff_aml_vals(qty, unit_valuation_difference)
        if self.purchase_line_id:
            for vals in vals_list:
                vals["oca_purchase_line_id"] = self.purchase_line_id.id
        return vals_list

    @api.depends("purchase_line_id", "oca_purchase_line_id")
    def _compute_purchase_id(self):
        for rec in self:
            rec.purchase_order_id = (
                rec.purchase_line_id.order_id.id or rec.oca_purchase_line_id.order_id.id
            )
