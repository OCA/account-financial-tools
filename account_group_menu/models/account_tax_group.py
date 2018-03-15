# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    tax_ids = fields.One2many(
        'account.tax', 'tax_group_id',
        string='Taxes',
        help="Assigned taxes.")
