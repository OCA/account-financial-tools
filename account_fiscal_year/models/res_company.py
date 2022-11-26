#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import timedelta

from odoo import fields, models
from odoo.tools import date_utils


class ResCompany(models.Model):
    _inherit = "res.company"

    fiscal_year_date_from = fields.Date(
        string="Start Date of the Fiscal Year",
        compute="_compute_fiscal_year_dates",
        compute_sudo=True,
    )

    fiscal_year_date_to = fields.Date(
        string="End Date of the Fiscal Year",
        compute="_compute_fiscal_year_dates",
        compute_sudo=True,
    )

    def _compute_fiscal_year_dates(self):
        today = fields.Date.today()
        for company in self:
            res = company.compute_fiscalyear_dates(today)
            company.fiscal_year_date_from = res["date_from"]
            company.fiscal_year_date_to = res["date_to"]

    def compute_fiscalyear_dates(self, current_date):
        """Computes the start and end dates of the fiscal year
        where the given 'date' belongs to.

        :param current_date: A datetime.date/datetime.datetime object.
        :return: A dictionary containing:
            * date_from
            * date_to
            * [Optionally] record: The fiscal year record.
        """
        self.ensure_one()

        AccountFiscalYear = self.env["account.fiscal.year"]

        # Search a fiscal year record containing the date.
        fiscalyear = AccountFiscalYear._get_fiscal_year(
            self, current_date, current_date
        )

        if fiscalyear:
            return {
                "date_from": fiscalyear.date_from,
                "date_to": fiscalyear.date_to,
                "record": fiscalyear,
            }

        date_from, date_to = date_utils.get_fiscal_year(
            current_date,
            day=self.fiscalyear_last_day,
            month=int(self.fiscalyear_last_month),
        )

        # Search for fiscal year records reducing
        # the delta between the date_from/date_to.
        # This case could happen if there is a gap
        # between two fiscal year records.
        # E.g. two fiscal year records:
        # 2017-01-01 -> 2017-02-01 and 2017-03-01 -> 2017-12-31.
        # =>
        # The period 2017-02-02 - 2017-02-30 is not covered by a fiscal year record.

        fiscalyear_from = AccountFiscalYear._get_fiscal_year(self, date_from, date_from)

        if fiscalyear_from:
            date_from = fiscalyear_from.date_to + timedelta(days=1)

        fiscalyear_to = AccountFiscalYear._get_fiscal_year(self, date_to, date_to)

        if fiscalyear_to:
            date_to = fiscalyear_to.date_from - timedelta(days=1)

        return {
            "date_from": date_from,
            "date_to": date_to,
        }
