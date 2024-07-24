# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"
    _rec_name = "number"

    number = fields.Char(
        string="Asset Number",
        default="",
        index=True,
        copy=False,
    )
    use_sequence = fields.Boolean(related="profile_id.use_sequence")

    def validate(self):
        res = super().validate()
        for asset in self:
            asset_profile = asset.profile_id
            if (
                asset.number in [False, ""]
                and asset_profile.use_sequence
                and asset_profile.sequence_id
            ):
                asset.number = asset_profile.sequence_id.next_by_id()
        return res

    @api.model
    def _xls_acquisition_fields(self):
        acquisition_fields = super()._xls_acquisition_fields()
        acquisition_fields.insert(acquisition_fields.index("name"), "number")
        return acquisition_fields

    @api.model
    def _xls_active_fields(self):
        active_fields = super()._xls_active_fields()
        active_fields.insert(active_fields.index("name"), "number")
        return active_fields

    @api.model
    def _xls_removal_fields(self):
        removal_fields = super()._xls_removal_fields()
        removal_fields.insert(removal_fields.index("name"), "number")
        return removal_fields
