# Copyright 2020 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    property_repartition_line_account_id = fields.Many2one(
        "account.account",
        company_dependent=True,
        string="Default account to use in repartition lines",
    )
