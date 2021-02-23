# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountAsset(models.Model):

    _inherit = "account.asset"

    def _compute_entries(self, date_end, check_triggers=False):
        if self.env.context.get(
            "asset_batch_processing", False
        ) and not self.env.context.get("test_queue_job_no_delay", False):
            results = []
            log_error = ""
            for record in self:
                description = _("Creating move for asset with id %s to %s") % (
                    record.id,
                    date_end,
                )
                record.with_delay(description=description)._compute_entries(
                    date_end, check_triggers=check_triggers
                )
            return results, log_error
        else:
            return super(AccountAsset, self)._compute_entries(
                date_end, check_triggers=check_triggers
            )
