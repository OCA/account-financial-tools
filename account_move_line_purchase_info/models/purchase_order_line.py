# Copyright 2019-2020 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends("order_line.invoice_lines.move_id")
    def _compute_invoice(self):
        """Overwritten compute to avoid show all Journal Entries with
        purchase_order_line as invoice_lines One2many would take them into account."""
        for order in self:
            invoices = order.mapped("order_line.invoice_lines.move_id").filtered(
                lambda m: m.is_invoice(include_receipts=True)
            )
            order.invoice_ids = [(6, 0, invoices.ids)]
            order.invoice_count = len(invoices)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def name_get(self):
        result = []
        orig_name = dict(super(PurchaseOrderLine, self).name_get())
        for line in self:
            name = orig_name[line.id]
            if self.env.context.get("po_line_info", False):
                name = "[{}] {} ({})".format(
                    line.order_id.name, name, line.order_id.state
                )
            result.append((line.id, name))
        return result
