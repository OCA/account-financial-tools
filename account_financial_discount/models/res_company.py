# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    financial_discount_revenue_account_id = fields.Many2one(
        'account.account', string='Financial discount writeoff revenue account'
    )

    financial_discount_expense_account_id = fields.Many2one(
        'account.account', string='Financial discount writeoff expense account'
    )
