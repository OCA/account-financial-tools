# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    account_ids = fields.Many2many(
        'account.account', 'account_account_account_tag',
        string='Accounts',
        help="Assigned accounts for custom reporting")
    tax_ids = fields.Many2many(
        'account.tax', 'account_tax_account_tag',
        string='Taxes',
        help="Assigned taxes for custom reporting")
