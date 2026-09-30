# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    # Plain stored m2o mirror of the core tag_ids m2m, so that accounts
    # remain searchable and groupable by tag from the account side, like
    # the account group search this module provided before Odoo 20.0.
    # Computed from tag_ids so that it follows every change of the m2m
    # (including from the tag side) and is filled on install.
    tag_id = fields.Many2one(
        comodel_name="account.account.tag",
        compute="_compute_tag_id",
        store=True,
        index="btree",
    )

    @api.depends("tag_ids")
    def _compute_tag_id(self):
        for account in self:
            account.tag_id = account.tag_ids[:1]
