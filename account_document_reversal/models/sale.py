# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("invoice_lines.move_id.state", "invoice_lines.quantity")
    def _get_invoice_qty(self):
        """ Cancel Reversal Entry is of type "entry", correction is needed """
        res = super()._get_invoice_qty()
        for line in self:
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.cancel_reversal:
                    if invoice_line.move_id.type == "out_invoice":
                        uom = invoice_line.product_uom_id
                        line.qty_invoiced -= uom._compute_quantity(
                            invoice_line.quantity, line.product_uom
                        )
                    elif invoice_line.move_id.type == "out_refund":
                        uom = invoice_line.product_uom_id
                        line.qty_invoiced += uom._compute_quantity(
                            invoice_line.quantity, line.product_uom
                        )
        return res
