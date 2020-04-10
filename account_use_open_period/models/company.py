# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

class ResCompany(models.Model):
    _inherit = "res.company"

    @api.multi
    def _check_last_lock_date(self):
        if not self.period_lock_date:
            return fields.Date.today()
        lock_to_date = min(
            self.period_lock_date,
            self.fiscalyear_lock_date) or False
        next_month = datetime.strptime(
            lock_to_date,
            DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=+1)
        days_next_month = calendar.monthrange(next_month.year,
                                              next_month.month)
        next_month_first_day = next_month.replace(
            day=1)
        next_month_last_day = next_month.replace(
            day=days_next_month[1])
        return next_month_first_day.strftime(DEFAULT_SERVER_DATE_FORMAT), next_month_last_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
