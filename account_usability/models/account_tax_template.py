# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    def name_get(self):
        name_list = []
        type_tax_use = dict(
            self._fields["type_tax_use"]._description_selection(self.env)
        )
        tax_scope = dict(self._fields["tax_scope"]._description_selection(self.env))
        for record in self:
            name = record.name
            if self._context.get("append_type_to_tax_name"):
                name += " (%s)" % type_tax_use.get(record.type_tax_use)
            if record.tax_scope:
                name += " (%s)" % tax_scope.get(record.tax_scope)
            name_list += [(record.id, name)]
        return name_list
