# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_interim_account_line_vals(self, line, move, debit_interim_account):
        res = super()._prepare_interim_account_line_vals(
            line, move, debit_interim_account
        )
        if (
            not res.get("move_id", False)
            or not res.get("product_id", False)
            or not res.get("quantity", False)
        ):
            return res
        am = self.env["account.move"].browse(res["move_id"])
        sale_line_id = am.invoice_line_ids.filtered(
            lambda il: il.product_id.id == res["product_id"]
            and il.quantity == res["quantity"]
        ).mapped("sale_line_id")
        if sale_line_id and len(sale_line_id) == 1:
            res["sale_line_id"] = sale_line_id.id
        return res

    def _prepare_expense_account_line_vals(self, line, move, debit_interim_account):
        res = super()._prepare_expense_account_line_vals(
            line, move, debit_interim_account
        )
        if (
            not res.get("move_id", False)
            or not res.get("product_id", False)
            or not res.get("quantity", False)
        ):
            return res
        am = self.env["account.move"].browse(res["move_id"])
        sale_line_id = am.invoice_line_ids.filtered(
            lambda il: il.product_id.id == res["product_id"]
            and il.quantity == res["quantity"]
        ).mapped("sale_line_id")
        if sale_line_id and len(sale_line_id) == 1:
            res["sale_line_id"] = sale_line_id.id
        return res


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale Order Line",
        ondelete="set null",
        index=True,
        copy=False,
    )

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        related="sale_line_id.order_id",
        string="Sales Order",
        ondelete="set null",
        store=True,
        index=True,
        copy=False,
    )
