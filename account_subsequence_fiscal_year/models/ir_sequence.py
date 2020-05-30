# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def _create_date_range_seq(self, date):
        AccountFiscalYear = self.env["account.fiscal.year"]
        IrSequenceDateRange = self.env["ir.sequence.date_range"]
        if self._context.get("account_sequence", False)\
                and self.company_id\
                and self.company_id.account_subsequence_method:

            method = self.company_id.account_subsequence_method
            object_date = fields.Date.from_string(date)

            if method == "company_setting":
                base_date = datetime.date(
                    object_date.year,
                    int(self.company_id.fiscalyear_last_month),
                    int(self.company_id.fiscalyear_last_day),
                )
                if object_date <= base_date:
                    date_from = base_date + relativedelta(years=-1, days=1)
                    date_to = base_date
                else:
                    date_from = base_date + relativedelta(days=1)
                    date_to = base_date + relativedelta(years=1)

            elif method == "fiscal_year_setting":
                fiscal_years = AccountFiscalYear.search(
                    [("date_to", ">=", object_date.strftime("%Y-%m-%d"))],
                    order="date_from desc",
                    limit=1
                )
                if not fiscal_years or fiscal_years[0].date_from > object_date:
                    raise ValidationError(_(
                        "You can not post an accounting entry for the"
                        " date %s because there is no fiscal year defined at"
                        " this date.") % (date))
                date_from = fiscal_years[0].date_from
                date_to = fiscal_years[0].date_to

            # Create and return new sequence
            return IrSequenceDateRange.sudo().create({
                'sequence_id': self.id,
                'date_from': date_from,
                'date_to': date_to,
            })

        return super()._create_date_range_seq(date)
