from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends("order_line.invoice_lines.move_id")
    def _compute_invoice(self):
        """Overwritten compute to avoid show all Journal Entries with
        purchase_order_line as invoice_lines One2many would take them into account."""
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda m: m.is_invoice(include_receipts=True)
            )
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)
