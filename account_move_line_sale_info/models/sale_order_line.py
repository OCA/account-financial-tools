# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def name_get(self):
        result = []
        orig_name = dict(super(SaleOrderLine, self).name_get())
        for line in self:
            name = orig_name[line.id]
            if self.env.context.get("so_line_info", False):
                name = "[{}] {} - ({})".format(
                    line.order_id.name, line.product_id.name, line.order_id.state
                )
            result.append((line.id, name))
        return result

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res["sale_id"] = self.order_id.id
        res["sale_line_id"] = self.id
        return res


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super()._prepare_invoice_values(order, name, amount, so_line)
        res["sale_id"] = order.id
        res["sale_line_id"] = so_line.id
        return res
