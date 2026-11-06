# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    fiscal_month = fields.Boolean(string="Is fiscal month?", readonly=True)

    def unlink(self):
        protected_record = self.env.ref(
            "account_fiscal_month.date_range_fiscal_month", raise_if_not_found=False
        )
        return super(DateRangeType, self - protected_record).unlink()
