# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        res = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        for i, vals in enumerate(res):
            am = self.env["account.move"].browse(vals["move_id"])
            sale_line_id = am.invoice_line_ids.filtered(
                lambda il: il.product_id.id == vals["product_id"]
                and il.quantity == vals["quantity"]
            ).mapped("sale_line_ids")
            if sale_line_id and len(sale_line_id) == 1:
                res[i]["sale_line_id"] = sale_line_id.id
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

    def _copy_data_extend_business_fields(self, values):
        # Same way Odoo standard does for purchase_line_id field
        res = super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values["sale_line_id"] = self.sale_line_id.id
        return res
