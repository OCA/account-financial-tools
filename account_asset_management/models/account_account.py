# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = "account.account"

    asset_profile_id = fields.Many2one(
        comodel_name="account.asset.profile",
        string="Asset Profile",
        check_company=True,
        company_dependent=True,
        help="Default Asset Profile when creating invoice lines with this account.",
    )

    @api.constrains("asset_profile_id")
    def _check_asset_profile(self):
        for account in self:
            if (
                account.asset_profile_id
                and account.asset_profile_id.account_asset_id != account
            ):
                raise ValidationError(
                    self.env._(
                        "The Asset Account defined in the Asset Profile "
                        "must be equal to the account."
                    )
                )

    def _get_asset_profile_for_company(self, company=None):
        """Return the asset profile for ``company``, walking ``parent_id`` if unset.

        ``asset_profile_id`` is ``company_dependent``: Odoo's SQL fallback chain
        is ``COALESCE(col->company_id, ir.default)`` — it does *not* walk
        ``res.company.parent_id``. In an Odoo 18+ branches setup, a child
        company with no own entry on a shared account would resolve to
        ``ir.default`` instead of inheriting the parent's choice. This helper
        restores the expected inheritance for branch hierarchies.
        """
        self.ensure_one()
        company = company or self.env.company
        seen = set()
        current = company
        while current and current.id not in seen:
            seen.add(current.id)
            profile = self.with_company(current).asset_profile_id
            if profile:
                return profile
            current = current.parent_id
        return self.env["account.asset.profile"]
