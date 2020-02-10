# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class AccountFiscalYear(models.Model):
    _inherit = "account.fiscal.year"

    @api.model
    def create(self, vals):
        date_from = datetime.strptime(vals.get("date_from"), "%Y-%m-%d")
        date_to = datetime.strptime(vals.get("date_to"), "%Y-%m-%d")
        if not date_to == date_from + relativedelta(years=1, days=-1):
            recompute_vals = {
                "reason": "creation of fiscalyear %s" % vals.get("name"),
                "company_id": vals.get("company_id") or self.env.user.company_id.id,
                "date_trigger": time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "state": "open",
            }
            self.env["account.asset.recompute.trigger"].sudo().create(recompute_vals)
        return super().create(vals)

    def write(self, vals):
        if vals.get("date_from") or vals.get("date_to"):
            for fy in self:
                recompute_vals = {
                    "reason": "duration change of fiscalyear %s" % fy.name,
                    "company_id": fy.company_id.id,
                    "date_trigger": time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    "state": "open",
                }
                self.env["account.asset.recompute.trigger"].sudo().create(
                    recompute_vals
                )
        return super().write(vals)
