# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    def write(self, vals):
        FptTemplate = self.env["account.fiscal.position.tax.template"]
        if "active" in vals and not vals.get("active"):
            # Disable account.tax.template should disable
            # account.fiscal.position.tax.template associated
            fptTemplates = FptTemplate.search(
                [
                    "|",
                    ("tax_src_id", "in", self.ids),
                    ("tax_dest_id", "in", self.ids),
                ]
            )
            fptTemplates.write({"active": False})
        return super().write(vals)
