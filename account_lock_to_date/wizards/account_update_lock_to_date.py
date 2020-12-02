# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError


class AccountUpdateLockToDate(models.TransientModel):
    _name = "account.update.lock_to_date"
    _description = "Account Update Lock_to_date"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    period_lock_to_date = fields.Date(
        string="Lock To Date for Non-Advisers",
        help="Only users with the 'Adviser' role can edit accounts after "
        "and inclusive of this date. Use it for period locking inside an "
        "open fiscal year, for example.",
    )
    fiscalyear_lock_to_date = fields.Date(
        string="Lock To Date",
        help="No users, including Advisers, can edit accounts after and "
        "inclusive of this date. Use it for fiscal year locking for "
        "example.",
    )

    @api.model
    def default_get(self, field_list):
        res = super(AccountUpdateLockToDate, self).default_get(field_list)
        company = self.env.user.company_id
        res.update(
            {
                "company_id": company.id,
                "period_lock_to_date": company.period_lock_to_date,
                "fiscalyear_lock_to_date": company.fiscalyear_lock_to_date,
            }
        )
        return res

    def _check_execute_allowed(self):
        self.ensure_one()
        has_adviser_group = self.env.user.has_group("account.group_account_manager")
        if not (has_adviser_group or self.env.uid == SUPERUSER_ID):
            raise ValidationError(_("You are not allowed to execute this action."))

    def execute(self):
        self.ensure_one()
        self._check_execute_allowed()
        self.company_id.sudo().write(
            {
                "period_lock_to_date": self.period_lock_to_date,
                "fiscalyear_lock_to_date": self.fiscalyear_lock_to_date,
            }
        )
