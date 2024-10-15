# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    vehicle_id = fields.Many2one(
        "fleet.vehicle", inverse="_inverse_vehicle", copy=False
    )

    def _inverse_vehicle(self):
        for asset in self:
            asset.vehicle_id.asset_id = asset
            # Remove asset from other vehicles
            vehicles = self.env["fleet.vehicle"].search(
                [("asset_id", "=", asset.id), ("id", "!=", asset.vehicle_id.id)]
            )
            if vehicles:
                vehicles.write({"asset_id": False})

    def action_open_vehicle(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "fleet.vehicle",
            "res_id": self.vehicle_id.id,
            "view_ids": [(False, "form")],
            "view_mode": "form",
        }
