# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        """Add repair_order_id to invoice line vals when available."""
        vals = super()._prepare_invoice_line(**optional_values)

        repair_orders = (
            self.env["repair.order"]
            .sudo()
            .search([("sale_order_id", "=", self.order_id.id)])
        )

        if len(repair_orders) == 1:
            vals["repair_order_id"] = repair_orders.id

        return vals
