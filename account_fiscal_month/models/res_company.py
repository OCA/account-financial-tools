# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def find_daterange_fm(self, date_str):
        self.ensure_one()
        fm_id = self.env.ref("account_fiscal_month.date_range_fiscal_month")
        domain = [
            ("type_id", "=", fm_id.id),
            ("date_start", "<=", date_str),
            ("date_end", ">=", date_str),
        ]
        # Add company filter only if company_id field exists on date.range
        if "company_id" in self.env["date.range"]._fields:
            domain.extend(
                ["|", ("company_id", "=", self.id), ("company_id", "=", False)]
            )
            order = "company_id asc"
        else:
            order = "date_start desc"
        return self.env["date.range"].search(domain, limit=1, order=order)
