# Copyright 2021 Opener B.V. <stefan@opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    account_root_group_id = fields.Many2one(
        comodel_name="account.group", string="Account Root Group",
        related="account_id.root_group_id",
        index=True, readonly=True, store=True)
    account_sub_group_id = fields.Many2one(
        comodel_name="account.group", string="Account Sub Group",
        related="account_id.sub_group_id",
        index=True, readonly=True, store=True)
