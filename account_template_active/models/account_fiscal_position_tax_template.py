# Copyright (C) 2019-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPositionTaxTemplate(models.Model):
    _inherit = "account.fiscal.position.tax.template"

    active = fields.Boolean("Active", default=True)

    def write(self, vals):
        TaxTemplate = self.env["account.tax.template"]
        if vals.get("active", False):
            # enable account.fiscal.position.tax.template should enable
            # related account.tax.template
            tax_ids = set(
                self.mapped("tax_src_id").ids + self.mapped("tax_dest_id").ids
            )
            taxTemplates = TaxTemplate.browse(tax_ids)
            taxTemplates.write({"active": True})
        return super().write(vals)
