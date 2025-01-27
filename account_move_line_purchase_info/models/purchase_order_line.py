# Copyright 2019-2020 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    stock_invoice_lines = fields.One2many(
        "account.move.line", "oca_purchase_line_id", readonly=True, copy=False
    )

    @api.depends("name", "order_id.name", "order_id.state")
    @api.depends_context("po_line_info")
    def _compute_display_name(self):
        if not self.env.context.get("po_line_info", False):
            return super()._compute_display_name()
        for line in self:
            line.display_name = (
                f"[{line.order_id.name}] {line.name} ({line.order_id.state})"
            )
