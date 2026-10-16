# Copyright 2015-2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    cost_center_id = fields.Many2one("account.cost.center", readonly=True)

    def _select(self):
        return (
            super(AccountInvoiceReport, self)._select()
            + ", line.cost_center_id as cost_center_id"
        )
