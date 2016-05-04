# -*- coding: utf-8 -*-
# © 2009-2016 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ResCompany(models.Model):
    """override company to add currency update"""

    _inherit = "res.company"

    @api.multi
    def button_refresh_currency(self):
        """Refresh the currencies rates"""
        self.ensure_one()
        self.services_to_use.refresh_currency()

    # Activate the currency update
    auto_currency_up = fields.Boolean(
        string='Automatic Update',
        help="Automatic update of the currencies for this company")
    # List of services to fetch rates
    services_to_use = fields.One2many(
        'currency.rate.update.service',
        'company_id',
        string='Currency update services')
