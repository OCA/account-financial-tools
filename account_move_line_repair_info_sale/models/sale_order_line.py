# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        """Add repair_order_id to invoice line vals when available."""
        vals = super()._prepare_invoice_line(**optional_values)
        # Repair parts are invoiced through sale order lines linked to the
        # repair stock moves, which gives the exact repair order per line.
        repair_orders = self.sudo().move_ids.repair_id
        if len(repair_orders) != 1:
            repair_orders = self.order_id.sudo().repair_order_ids
        if len(repair_orders) == 1:
            vals["repair_order_id"] = repair_orders.id
        return vals
