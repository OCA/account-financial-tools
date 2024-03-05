# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):

    _inherit = "account.account"

    @api.constrains("code")
    def _disable_code_modification(self):
        line = (
            self.env["account.move.line"]
            .sudo()
            .search([("account_id", "in", self.ids)], limit=1)
        )
        if line:
            raise ValidationError(
                _("You cannot change the code of account which contains journal items.")
            )
