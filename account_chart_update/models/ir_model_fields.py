# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    def name_get(self):
        """Return special label when showing fields in chart update wizard."""
        if self.env.context.get("account_chart_update"):
            res = []
            for record in self:
                res.append(
                    (record.id, "{} ({})".format(record.field_description, record.name))
                )
            return res
        return super(IrModelFields, self).name_get()
