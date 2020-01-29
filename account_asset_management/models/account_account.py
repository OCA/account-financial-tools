# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = "account.account"

    asset_profile_id = fields.Many2one(
        comodel_name="account.asset.profile",
        string="Asset Profile",
        help="Default Asset Profile when creating invoice lines " "with this account.",
    )

    @api.constrains("asset_profile_id")
    def _check_asset_profile(self):
        for account in self:
            if (
                account.asset_profile_id
                and account.asset_profile_id.account_asset_id != account
            ):
                raise ValidationError(
                    _(
                        "The Asset Account defined in the Asset Profile "
                        "must be equal to the account."
                    )
                )
