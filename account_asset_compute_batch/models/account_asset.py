# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    def _get_asset_line_domain(self, date_end):
        domain = super()._get_asset_line_domain(date_end)
        if self.env.context.get("compute_profile_ids"):
            domain.append(
                ("asset_id.profile_id", "in", self.env.context["compute_profile_ids"])
            )
        return domain
