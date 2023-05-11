# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    fiscal_month = fields.Boolean(string="Is fiscal month?", readonly=True)

    def unlink(self):
        date_range_type_fm = self.env.ref(
            "account_fiscal_month.date_range_fiscal_month"
        )
        if date_range_type_fm.id in self.ids:
            raise UserError(_("You can't delete date range type: " "Fiscal month"))
        return super().unlink()
