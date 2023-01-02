# Copyright 2022-2023 Moduon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    # Overridden fields
    code_prefix = fields.Char(
        compute="_compute_code_prefix",
        store=True,
        help="Account code without trailing zeros.",
    )

    @api.depends("code")
    def _compute_code_prefix(self):
        """Get account code without trailing zeros."""
        for one in self:
            one.code_prefix = one.code and one.code.rstrip("0")
