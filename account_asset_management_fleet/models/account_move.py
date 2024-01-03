# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_asset_vals(self, aml):
        result = super()._prepare_asset_vals(aml)
        if aml.vehicle_id:
            if aml.asset_profile_id and aml.vehicle_id.asset_id and not aml.asset_id:
                raise UserError(
                    _(
                        "You cannot create a new asset for this vehicle, "
                        "because it already has an asset."
                    )
                )
            elif (
                aml.asset_id
                and aml.vehicle_id.asset_id
                and aml.asset_id != aml.vehicle_id.asset_id
            ):
                raise UserError(
                    _("The specified asset does not match the vehicle's current asset.")
                )
            else:
                result["vehicle_id"] = aml.vehicle_id
        return result
