# Copyright 2021 Opener B.V. <stefan@opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    root_group_id = fields.Many2one(
        comodel_name="account.group", string="Root Group",
        compute="_compute_account_groups", index=True, store=True)
    sub_group_id = fields.Many2one(
        comodel_name="account.group", string="Sub Group",
        compute="_compute_account_groups", index=True, store=True)

    @api.depends("group_id")
    def _compute_account_groups(self):
        """Provide the root and sub group for each account"""
        if not self.ids:
            return
        for account in self:
            sub_group = self.env["account.group"]
            root_group = account.group_id
            while root_group.parent_id:
                sub_group = root_group
                root_group = sub_group.parent_id
            account.root_group_id = root_group
            account.sub_group_id = sub_group
