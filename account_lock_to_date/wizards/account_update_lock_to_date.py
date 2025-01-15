# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

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
    is_lock_to_date_periodic = fields.Boolean(
        string="Express the interval as number of days.",
        help="Express the interval as number of days.",
        default=False,
    )
    lock_to_date_periodicity_advisers = fields.Integer(
        string="Periodicity for Advisers",
        default="30",
        help="Number of days after which all users, including advisers, "
        "cannot write in accounting.",
    )
    lock_to_date_periodicity = fields.Integer(
        string="Periodicity for Non-Advisers",
        default="15",
        help="Number of days after which non-advisers cannot write in accounting.",
    )

    @api.model
    def default_get(self, field_list):
        res = super(AccountUpdateLockToDate, self).default_get(field_list)
        company = self.env.user.company_id
        res.update(
            {
                "company_id": company.id,
                "is_lock_to_date_periodic": company.is_lock_to_date_periodic,
                "period_lock_to_date": company.period_lock_to_date,
                "fiscalyear_lock_to_date": company.fiscalyear_lock_to_date,
                "lock_to_date_periodicity_advisers": company.lock_to_date_periodicity_advisers,
                "lock_to_date_periodicity": company.lock_to_date_periodicity,
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
        if self.is_lock_to_date_periodic:
            if (
                not self.lock_to_date_periodicity_advisers
                or not self.lock_to_date_periodicity
            ):
                raise ValidationError(
                    _("Please input a number of days for the lock to date.")
                )
            self.company_id.sudo().write(
                {
                    "is_lock_to_date_periodic": self.is_lock_to_date_periodic,
                    "lock_to_date_periodicity": self.lock_to_date_periodicity,
                    "lock_to_date_periodicity_advisers": self.lock_to_date_periodicity_advisers,
                    "period_lock_to_date": datetime.now().date()
                    + timedelta(days=self.lock_to_date_periodicity),
                    "fiscalyear_lock_to_date": datetime.now().date()
                    + timedelta(days=self.lock_to_date_periodicity_advisers),
                }
            )
        else:
            self.company_id.sudo().write(
                {
                    "is_lock_to_date_periodic": self.is_lock_to_date_periodic,
                    "lock_to_date_periodicity": self.lock_to_date_periodicity,
                    "lock_to_date_periodicity_advisers": self.lock_to_date_periodicity_advisers,
                    "period_lock_to_date": self.period_lock_to_date,
                    "fiscalyear_lock_to_date": self.fiscalyear_lock_to_date,
                }
            )
