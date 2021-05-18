# Copyright (C) 2018-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPositionAccountTemplate(models.Model):
    _inherit = "account.fiscal.position.account.template"

    active = fields.Boolean("Active", default=True)

    def write(self, vals):
        AccountTemplate = self.env["account.account.template"]
        if vals.get("active", False):
            # enable account.fiscal.position.account.template should enable
            # related account.account.template
            account_ids = set(
                self.mapped("account_src_id").ids + self.mapped("account_dest_id").ids
            )
            accountTemplates = AccountTemplate.browse(account_ids)
            accountTemplates.write({"active": True})
        return super().write(vals)
