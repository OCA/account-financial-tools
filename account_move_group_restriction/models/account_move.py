# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import Command, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    account_security_group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="account_move_res_groups_rel",
        column1="move_id",
        column2="group_id",
        string="Account Access Groups",
        compute="_compute_account_security_group_ids",
        compute_sudo=True,
        store=True,
        help=(
            "Union of the security groups configured on the accounts used "
            "on this journal entry. Used by record rules to restrict access: "
            "if any line uses a restricted account, the whole move becomes "
            "visible only to users in at least one of these groups."
        ),
    )

    @api.depends("line_ids.account_id.security_group_ids")
    def _compute_account_security_group_ids(self):
        for move in self:
            groups = move.mapped("line_ids.account_id.security_group_ids")
            move.account_security_group_ids = [Command.set(groups.ids)]
