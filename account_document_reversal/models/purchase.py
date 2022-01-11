# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.depends("invoice_lines.move_id.state", "invoice_lines.quantity")
    def _compute_qty_invoiced(self):
        """ Cancel Reversal Entry is of type "entry", correction is needed """
        res = super()._compute_qty_invoiced()
        for line in self:
            for inv_line in line.invoice_lines:
                if inv_line.move_id.cancel_reversal:
                    if inv_line.move_id.type == "in_invoice":
                        line.qty_invoiced -= inv_line.product_uom_id._compute_quantity(
                            inv_line.quantity, line.product_uom
                        )
                    elif inv_line.move_id.type == "in_refund":
                        line.qty_invoiced += inv_line.product_uom_id._compute_quantity(
                            inv_line.quantity, line.product_uom
                        )
        return res
