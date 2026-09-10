# Copyright 2020-23 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        # Resolve each COGS val dict back to its originating invoice line via
        # the ``cogs_origin_id`` FK written by core stock_account. This
        # replaces a product_id + quantity heuristic that silently dropped
        # propagation whenever two invoice lines on the same document shared
        # the same product and quantity -- e.g. credit notes with a refund
        # line and a free replacement line both at qty=-1.
        res = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        origin_ids = {
            vals["cogs_origin_id"] for vals in res if vals.get("cogs_origin_id")
        }
        if not origin_ids:
            return res
        origins = self.env["account.move.line"].browse(origin_ids)
        sale_line_by_origin = {
            line.id: line.sale_line_id.id for line in origins if line.sale_line_id
        }
        for vals in res:
            sol_id = sale_line_by_origin.get(vals.get("cogs_origin_id"))
            if sol_id:
                vals["sale_line_id"] = sol_id
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
        res = super()._copy_data_extend_business_fields(values)
        values["sale_line_id"] = self.sale_line_id.id
        return res
