# Copyright 2024 ForgeFlow SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    country_group_id = fields.Many2one("res.country.group", readonly=True)

    def _select(self):
        return (
            super(AccountInvoiceReport, self)._select()
            + ", line.country_group_id as country_group_id"
        )
