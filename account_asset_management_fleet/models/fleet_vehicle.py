# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FleetVehicle(models.Model):

    _inherit = "fleet.vehicle"

    asset_id = fields.Many2one("account.asset", readonly=True, copy=False)
    asset_code = fields.Char(string="Asset Code", related="asset_id.code")
    net_car_value = fields.Float(
        store=True, readonly=False, compute="_compute_asset_values"
    )
    residual_value = fields.Float(
        store=True, readonly=False, compute="_compute_asset_values"
    )

    @api.depends("asset_id")
    def _compute_asset_values(self):
        if self.asset_id:
            self.net_car_value = self.asset_id.purchase_value
            self.residual_value = self.asset_id.value_residual
