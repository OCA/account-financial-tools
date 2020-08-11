# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FinancialDiscountSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    financial_discount_revenue_account_id = fields.Many2one(
        'account.account',
        string='Financial discount revenue write-off account',
        related='company_id.financial_discount_revenue_account_id',
        readonly=False,
    )

    financial_discount_expense_account_id = fields.Many2one(
        'account.account',
        string='Financial discount expense write-off account',
        related='company_id.financial_discount_expense_account_id',
        readonly=False,
    )
