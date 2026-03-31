# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountGroup(models.Model):
    _inherit = "account.group"

    account_ids = fields.One2many(
        comodel_name="account.account",
        inverse_name="group_id",
        string="Accounts",
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        self.env["account.account"]._invalidate_group_to_accounts_cache()
        return res

    def write(self, vals):
        res = super().write(vals)
        if "code_prefix_start" in vals or "code_prefix_end" in vals:
            self.env["account.account"]._invalidate_group_to_accounts_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env["account.account"]._invalidate_group_to_accounts_cache()
        return res
