# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_subsequence_method = fields.Selection(
        string="Accounting Subsequences Method",
        selection=[
            ("company_setting", "Based on Company Settings"),
            ("fiscal_year_setting", "Based on Fiscal Years Settings"),
        ])
