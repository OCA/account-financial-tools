# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountUpdateLockDate(models.TransientModel):
    _name = "account.update.lock_date"
    _description = "Account Update Lock_date"

    company_id = fields.Many2one(comodel_name="res.company", required=True)
    period_lock_date = fields.Date(
        string="Lock Date for Non-Advisers",
        help="Only users with the 'Adviser' role can edit accounts prior to "
        "and inclusive of this date. Use it for period locking inside an "
        "open fiscal year, for example.",
    )
    fiscalyear_lock_date = fields.Date(
        string="Lock Date for All Users",
        help="No users, including Advisers, can edit accounts prior to and "
        "inclusive of this date. Use it for fiscal year locking for "
        "example.",
    )
    tax_lock_date = fields.Date(
        string="Tax Lock Date",
        help="No users can edit journal entries related to a tax prior and "
        "inclusive of this date.",
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        company = self.env.company
        res.update(
            {
                "company_id": company.id,
                "period_lock_date": company.period_lock_date,
                "fiscalyear_lock_date": company.fiscalyear_lock_date,
                "tax_lock_date": company.tax_lock_date,
            }
        )
        return res

    def _check_execute_allowed(self):
        self.ensure_one()
        has_adviser_group = self.env.user.has_group("account.group_account_manager")
        if not (has_adviser_group or self.env.user._is_admin()):
            raise UserError(_("You are not allowed to execute this action."))

    def execute(self):
        self.ensure_one()
        self._check_execute_allowed()
        self.company_id.sudo().write(
            {
                "period_lock_date": self.period_lock_date,
                "fiscalyear_lock_date": self.fiscalyear_lock_date,
                "tax_lock_date": self.tax_lock_date,
            }
        )
