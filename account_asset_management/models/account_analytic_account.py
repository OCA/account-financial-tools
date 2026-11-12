# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    def unlink(self):
        """Prevent deleting an analytic account still used by an asset.

        The analytic distribution of an asset is a JSON field, therefore no
        foreign key prevents the deletion of an account referenced there. The
        dead reference is then copied as is into the depreciation entries, and
        Odoo silently drops the unknown account when generating the analytic
        lines: the entries end up with an analytic distribution pointing to a
        non-existing account.
        """
        asset_model = self.env["account.asset"].sudo()
        profile_model = self.env["account.asset.profile"].sudo()
        for account in self:
            domain = [("analytic_distribution", "in", [str(account.id)])]
            if asset_model.search(domain, limit=1) or profile_model.search(
                domain, limit=1
            ):
                raise UserError(
                    _(
                        "The analytic account %s is used by an asset and cannot "
                        "be deleted. Archive it instead.",
                        account.display_name,
                    )
                )
        return super().unlink()
