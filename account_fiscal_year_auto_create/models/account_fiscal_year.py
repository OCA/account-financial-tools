# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, models


class AccountFiscalYear(models.Model):
    _inherit = "account.fiscal.year"

    @api.model
    def cron_auto_create(self):
        companies = self.env["res.company"].search([])
        for company in companies:
            last_fiscal_year = self.search(
                [("company_id", "=", company.id)], order="date_to desc", limit=1
            )

            if last_fiscal_year and (
                last_fiscal_year.date_to < datetime.now().date() + relativedelta(days=1)
            ):
                self.create(last_fiscal_year._prepare_next_fiscal_year())

    def _prepare_next_fiscal_year(self):
        self.ensure_one()
        # try to generate a new name, based on the previous
        # name replacing YYYY pattern by YYYY+1 value
        # - "FY 2018" will be replace by "FY 2019"
        # - "FY 2018-2019" will be replace by "FY 2019-2020"
        new_name = self.name.replace(
            str(self.date_to.year), str(self.date_to.year + 1)
        ).replace(str(self.date_from.year), str(self.date_from.year + 1))
        if self.search(
            [("name", "=", new_name), ("company_id", "=", self.company_id.id)]
        ):
            # the replace process fail to guess a correct unique name
            new_name = _(
                "FY %(date_to)s - %(date_from)s",
                date_to=str(self.date_to),
                date_from=str(self.date_from),
            )
        # compute new dates, handling leap years
        new_date_from = self.date_to + relativedelta(days=1)
        new_date_to = new_date_from + relativedelta(years=1, days=-1)
        return {
            "name": new_name,
            "company_id": self.company_id.id,
            "date_from": new_date_from.strftime("%Y-%m-%d"),
            "date_to": new_date_to.strftime("%Y-%m-%d"),
        }
