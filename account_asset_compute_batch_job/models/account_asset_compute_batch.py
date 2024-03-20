# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class AssetComputeBatch(models.Model):
    _inherit = "account.asset.compute.batch"

    job_ids = fields.Many2many(
        comodel_name="queue.job",
        column1="batch_id",
        column2="job_id",
        relation="asset_batch_job_rel",
        copy=False,
    )
    job_current = fields.Many2one(comodel_name="queue.job", readonly=True)
    job_state = fields.Selection(string="Job State", related="job_current.state")

    def action_compute_job(self):
        self.ensure_one()
        queue_obj = self.env["queue.job"]
        if not self.env.context.get("job_uuid") and not self.env.context.get(
            "test_queue_job_no_delay"
        ):
            description = _("Creating jobs to create moves for assets to %s") % (
                self.date_end,
            )
            new_delay = self.with_delay(description=description).action_compute()
            job = queue_obj.search([("uuid", "=", new_delay.uuid)])
            self.job_ids = [(4, job.id)]
            self.job_current = job.id
            return "Job created with uuid {}".format(new_delay.uuid)
        return super().action_compute()

    def open_queue_job(self):
        self.ensure_one()
        action = {
            "name": _("Jobs"),
            "view_type": "tree",
            "view_mode": "list,form",
            "res_model": "queue.job",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.job_ids.ids)],
        }
        return action
