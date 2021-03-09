# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, fields, models
from odoo.exceptions import UserError


class UpdateJournalLockDatesWizard(models.TransientModel):
    _name = "update.journal.lock.dates.wizard"
    _description = "Mass Update Journal Lock Dates Wizard"

    period_lock_date = fields.Date(string="Lock Date for Non-Advisers")
    fiscalyear_lock_date = fields.Date(string="Lock Date")

    def _check_execute_allowed(self):
        self.ensure_one()
        has_adviser_group = self.env.user.has_group("account.group_account_manager")
        if not (has_adviser_group or self.env.uid == SUPERUSER_ID):
            raise UserError(_("You are not allowed to execute this action."))

    def action_update_lock_dates(self):
        self.ensure_one()
        self._check_execute_allowed()
        active_ids = self.env.context.get("active_ids", False)
        if active_ids:
            self.env["account.journal"].browse(active_ids).write(
                {
                    "period_lock_date": self.period_lock_date,
                    "fiscalyear_lock_date": self.fiscalyear_lock_date,
                }
            )
