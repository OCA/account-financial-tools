# Copyright 2024 Bernat Obrador(APSL-Nagarro)<bobrador@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange("asset_profile_id")
    def _onchange_asset_profile_id(self):
        if self.account_id and self.account_id.account_type == "asset_fixed":
            return
        super()._onchange_asset_profile_id()
