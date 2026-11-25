# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, fields, models
from odoo.exceptions import UserError


class UpdateJournalLockToDatesWizard(models.TransientModel):
    _name = "update.journal.lock.to.dates.wizard"
    _description = "Mass Update Journal Lock To Dates Wizard"

    fiscalyear_lock_to_date = fields.Date(string="Lock To Date")
    period_lock_to_date = fields.Date(string="Lock To Date for Non-Advisers")

    def _check_execute_allowed(self):
        self.ensure_one()
        has_adviser_group = self.env.user.has_group("account.group_account_manager")
        if not (has_adviser_group or self.env.uid == SUPERUSER_ID):
            raise UserError(self.env._("You are not allowed to execute this action."))

    def action_update_lock_to_dates(self):
        self.ensure_one()
        self._check_execute_allowed()
        active_ids = self.env.context.get("active_ids", False)
        if active_ids:
            self.env["account.journal"].browse(active_ids).write(
                {
                    "fiscalyear_lock_to_date": self.fiscalyear_lock_to_date,
                    "period_lock_to_date": self.period_lock_to_date,
                }
            )
