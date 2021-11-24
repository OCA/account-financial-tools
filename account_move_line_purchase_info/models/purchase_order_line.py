# Copyright 2019-2020 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


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
