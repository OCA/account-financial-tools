# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    amount_discount = fields.Monetary(
        'Financial Discount amount in company currency',
        currency_field='company_currency_id',
    )
    amount_discount_currency = fields.Monetary(
        'Financial Discount amount in an optional other currency if it is a '
        'multi-currency entry.'
    )
    date_discount = fields.Date('Financial Discount date')
    discount_tax_line_id = fields.Many2one('account.move.line')
    amount_discount_tax = fields.Monetary(currency_field='company_currency_id')
