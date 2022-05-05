# Copyright 2016-2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class AccountAssetCompute(models.TransientModel):

    _inherit = "account.asset.compute"

    batch_processing = fields.Boolean()

    def asset_compute(self):
        self.ensure_one()
        if not self.batch_processing:
            return super(AccountAssetCompute, self).asset_compute()
        if not self.env.context.get("job_uuid") and not self.env.context.get(
            "test_queue_job_no_delay"
        ):
            description = _("Creating jobs to create moves for assets to %s") % (
                self.date_end,
            )
            job = self.with_delay(description=description).asset_compute()
            return "Job created with uuid {}".format(job.uuid)
        else:
            return super(
                AccountAssetCompute, self.with_context(asset_batch_processing=True)
            ).asset_compute()
