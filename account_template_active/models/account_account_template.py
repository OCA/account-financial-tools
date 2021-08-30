# Copyright (C) 2015 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountAccountTemplate(models.Model):
    _inherit = "account.account.template"

    active = fields.Boolean(string="Active", default=True)

    def write(self, vals):
        FpaTemplate = self.env["account.fiscal.position.account.template"]
        if "active" in vals and not vals.get("active"):
            # Disable account.account.template should disable
            # account.fiscal.position.account.template associated
            fpaTemplates = FpaTemplate.search(
                [
                    "|",
                    ("account_src_id", "in", self.ids),
                    ("account_dest_id", "in", self.ids),
                ]
            )
            fpaTemplates.write({"active": False})
        return super().write(vals)
