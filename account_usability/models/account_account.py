# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    # Plain stored m2o mirror of the core tag_ids m2m (whose inverse is
    # not searchable), maintained by create/write below, so that accounts
    # remain searchable and groupable by tag from the account side, like
    # the account group search this module provided before Odoo 20.0.
    tag_id = fields.Many2one(
        comodel_name="account.account.tag",
        index="btree",
    )

    def _sync_tag_id_values(self):
        for account in self:
            account.tag_id = account.tag_ids[:1]

    @api.model_create_multi
    def create(self, vals_list):
        accounts = super().create(vals_list)
        accounts._sync_tag_id_values()
        return accounts

    def write(self, vals):
        res = super().write(vals)
        if "tag_ids" in vals:
            self._sync_tag_id_values()
        return res
