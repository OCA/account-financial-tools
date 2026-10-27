# Copyright 2019-2020 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.depends("name", "product_id.display_name", "order_id.name", "order_id.state")
    @api.depends_context("po_line_info")
    def _compute_display_name(self):
        if not self.env.context.get("po_line_info", False):
            return super()._compute_display_name()
        for line in self:
            name = (
                line.name
                or line.product_id.with_context(
                    formatted_display_name=False
                ).display_name
            )
            line.display_name = f"[{line.order_id.name}] {name} ({line.order_id.state})"
