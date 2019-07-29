# Copyright 2019 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def name_get(self):
        result = []
        orig_name = dict(super(PurchaseOrderLine, self).name_get())
        for line in self:
            name = orig_name[line.id]
            if self.env.context.get('po_line_info', False):
                name = "[%s] %s (%s)" % (line.order_id.name, name,
                                         line.order_id.state)
            result.append((line.id, name))
        return result
