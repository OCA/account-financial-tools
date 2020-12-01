# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import calendar
import time
from datetime import datetime
from time import mktime

from dateutil.relativedelta import relativedelta

from odoo import SUPERUSER_ID, _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class ResCompany(models.Model):
    _inherit = "res.company"

    period_lock_to_date = fields.Date(
        string="Lock To Date for Non-Advisers",
        help="Only users with the 'Adviser' role can edit "
        "accounts after this date. "
        "Use it for period locking inside an open fiscal year, "
        "for example.",
    )
    fiscalyear_lock_to_date = fields.Date(
        string="Lock To Date",
        help="No users, including Advisers, can edit accounts after "
        "this date. Use it for fiscal year locking for example.",
    )

    def write(self, vals):
        # fiscalyear_lock_date can't be set to a prior date
        if "fiscalyear_lock_to_date" in vals or "period_lock_to_date" in vals:
            self._check_lock_to_dates(vals)
        return super(ResCompany, self).write(vals)

    def _check_lock_to_dates(self, vals):
        """Check the lock to dates for the current companies.

        :param vals: The values passed to the write method.
        """
        period_lock_to_date = vals.get("period_lock_to_date")
        fiscalyear_lock_to_date = vals.get("fiscalyear_lock_to_date")

        next_month = datetime.now() + relativedelta(months=+1)
        days_next_month = calendar.monthrange(next_month.year, next_month.month)
        next_month = next_month.replace(day=days_next_month[1]).timetuple()
        next_month = datetime.fromtimestamp(mktime(next_month)).date()
        for company in self:
            old_fiscalyear_lock_to_date = company.fiscalyear_lock_to_date

            # The user attempts to remove the lock date for advisors
            if (
                old_fiscalyear_lock_to_date
                and not fiscalyear_lock_to_date
                and "fiscalyear_lock_to_date" in vals
                and not self._uid == SUPERUSER_ID
            ):
                raise ValidationError(
                    _(
                        "The lock date for advisors is "
                        "irreversible and can't be removed."
                    )
                )

            # The user attempts to set a lock date for advisors prior
            # to the previous one
            if (
                old_fiscalyear_lock_to_date
                and fiscalyear_lock_to_date
                and fiscalyear_lock_to_date > old_fiscalyear_lock_to_date
            ):
                raise ValidationError(
                    _(
                        "The new lock to date for advisors must be set after "
                        "the previous lock to date."
                    )
                )

            # In case of no new fiscal year in vals, fallback to the oldest
            if not fiscalyear_lock_to_date:
                if old_fiscalyear_lock_to_date:
                    fiscalyear_lock_to_date = old_fiscalyear_lock_to_date
                else:
                    continue

            # The user attempts to set a lock date for advisors after
            # the first day of next month
            if fiscalyear_lock_to_date < next_month:
                raise ValidationError(
                    _(
                        "You cannot lock a period that is not finished yet. "
                        "Please make sure that the lock date for advisors is "
                        "set at or after the last day of the next month."
                    )
                )

            # In case of no new period lock to date in vals,
            # fallback to the one defined in the company
            if not period_lock_to_date:
                if company.period_lock_date:
                    period_lock_to_date = time.strptime(
                        company.period_lock_to_date, DEFAULT_SERVER_DATE_FORMAT
                    )
                else:
                    continue

            # The user attempts to set a lock to date for advisors
            # prior to the lock to date for users
            if period_lock_to_date > fiscalyear_lock_to_date:
                raise ValidationError(
                    _(
                        "You cannot define stricter conditions on advisors "
                        "than on users. Please make sure that the lock date "
                        "on advisor is set after the lock date for users."
                    )
                )

    def _validate_fiscalyear_lock(self, values):
        res = super()._validate_fiscalyear_lock(values)
        if values.get("fiscalyear_lock_to_date"):
            nb_draft_entries = self.env["account.move"].search(
                [
                    ("company_id", "in", self.ids),
                    ("state", "=", "draft"),
                    ("date", ">=", values["fiscalyear_lock_to_date"]),
                ],
                limit=1,
            )
            if nb_draft_entries:
                raise ValidationError(
                    _(
                        "There are still unposted entries in the period to date"
                        " you want to lock. "
                        "You should either post or delete them."
                    )
                )
        return res
