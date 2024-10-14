# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAssetRemove(models.TransientModel):
    _inherit = "account.asset.remove"

    def remove(self):
        self.ensure_one()
        asset_id = self.env.context.get("active_id")
        asset = self.env["account.asset"].browse(asset_id)
        if asset.low_value:
            asset.write({"state": "removed", "date_remove": self.date_remove})
            return True
        return super().remove()
