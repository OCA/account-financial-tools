# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    security_group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="account_account_res_groups_rel",
        column1="account_id",
        column2="group_id",
        string="Access Groups",
        help=(
            "If set, only users belonging to at least one of these groups "
            "will be able to see journal items and journal entries "
            "posting on this account. "
            "If left empty, the account is visible to all accounting users."
        ),
    )
