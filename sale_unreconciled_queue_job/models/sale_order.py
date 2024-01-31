# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    reconcile_job_pending = fields.Boolean(compute="_compute_reconcile_job_pending")

    def _compute_reconcile_job_pending(self):
        for rec in self:
            job_task = "sale.order(%s,).action_reconcile()" % rec.id
            jobs = self.env["queue.job"].search(
                [
                    ("state", "not in", ("done", "failed")),
                    ("func_string", "=", job_task),
                ]
            )
            rec.reconcile_job_pending = bool(jobs)

    def action_reconcile(self):
        for rec in self:
            if not rec.reconcile_job_pending:
                return super(SaleOrder, rec).with_delay().action_reconcile()
