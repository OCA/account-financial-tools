# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResCompany(models.Model):

    _inherit = "res.company"

    def find_daterange_fm(self, date_str):
        self.ensure_one()
        fm_id = self.env.ref("account_fiscal_month.date_range_fiscal_month")
        return self.env["date.range"].search(
            [
                ("type_id", "=", fm_id.id),
                ("date_start", "<=", date_str),
                ("date_end", ">=", date_str),
                "|",
                ("company_id", "=", self.id),
                ("company_id", "=", False),
            ],
            limit=1,
            order="company_id asc",
        )
