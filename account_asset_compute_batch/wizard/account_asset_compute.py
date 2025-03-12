# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetCompute(models.TransientModel):
    _inherit = "account.asset.compute"

    use_batch = fields.Boolean(string="Create Batch", help="Use batch opton")
    batch_name = fields.Char(
        help="If batch name is specified, computation will be tracked by a batch",
    )
    description = fields.Char()
    profile_ids = fields.Many2many(
        comodel_name="account.asset.profile",
        string="Profiles",
    )
    delay_compute = fields.Boolean(string="Delay Compute Asset")

    def _prepare_asset_compute_batch(self):
        return {
            "date_end": self.date_end,
            "name": self.batch_name,
            "description": self.description,
            "profile_ids": [(4, profile.id) for profile in self.profile_ids],
        }

    def asset_compute(self):
        if not self.use_batch:
            return super().asset_compute()

        batch = self.env["account.asset.compute.batch"].create(
            self._prepare_asset_compute_batch()
        )
        if not self.delay_compute:
            batch.action_compute()
        return {
            "name": self.env._("Asset Compute Batch"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "account.asset.compute.batch",
            "res_id": batch.id,
        }
