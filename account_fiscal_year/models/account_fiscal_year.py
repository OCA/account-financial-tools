#  Copyright 2020 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class AccountFiscalYear(models.Model):
    _inherit = "account.fiscal.year"
    _description = "Fiscal Year"

    @api.model
    def _get_fiscal_year(self, company, date_from, date_to):
        """Return a fiscal year for the given company
        that contains the two dates. (or False if no fiscal years)
        matches the selection"""
        return self.search(
            [
                ("company_id", "=", company.id),
                ("date_from", "<=", date_from),
                ("date_to", ">=", date_to),
            ],
            limit=1,
        )
