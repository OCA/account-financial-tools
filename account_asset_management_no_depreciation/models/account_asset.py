# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.account_asset_management.models.account_asset import READONLY_STATES


class AccountAsset(models.Model):
    _inherit = "account.asset"

    no_depreciation = fields.Boolean(
        string="Non-Depreciation",
        compute="_compute_no_depreciation",
        readonly=False,
        store=True,
        states=READONLY_STATES,
        help="Check this if you do not want to compute depreciation.",
    )

    @api.depends("profile_id")
    def _compute_no_depreciation(self):
        for asset in self:
            asset.no_depreciation = asset.profile_id.no_depreciation

    def remove(self):
        self.ensure_one()
        if self.no_depreciation:
            self.write(
                {
                    "state": "removed",
                    "date_remove": self.date_remove or fields.Date.today(),
                }
            )
            return True
        else:
            return super().remove()

    def compute_depreciation_board(self):
        assets = self.filtered(lambda a: not a.no_depreciation)
        return super(AccountAsset, assets).compute_depreciation_board()
