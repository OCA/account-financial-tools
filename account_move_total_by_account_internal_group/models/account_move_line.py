# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Making standard field stored in order to do the calculations faster
    account_internal_group = fields.Selection(
        related="account_id.user_type_id.internal_group",
        string="Internal Group",
        readonly=True,
        store=True,
    )
