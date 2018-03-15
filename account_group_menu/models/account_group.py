# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountGroup(models.Model):
    _inherit = 'account.group'

    account_ids = fields.One2many(
        'account.account', 'group_id',
        string='Accounts',
        help="Assigned accounts.")
