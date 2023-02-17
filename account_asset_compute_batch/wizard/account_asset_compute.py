# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


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

    def asset_compute(self):
        if self.use_batch:
            vals = {
                "date_end": self.date_end,
                "name": self.batch_name,
                "description": self.description,
                "profile_ids": [(4, x.id) for x in self.profile_ids],
            }
            batch = self.env["account.asset.compute.batch"].create(vals)
            if not self.delay_compute:
                batch.action_compute()
            return {
                "name": _("Asset Compute Batch"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "account.asset.compute.batch",
                "res_id": batch.id,
            }
        return super().asset_compute()
