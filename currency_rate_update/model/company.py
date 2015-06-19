# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class res_company(models.Model):
    """override company to add currency update"""

    @api.multi
    def _compute_multi_curr_enable(self):
        "check if multi company currency is enabled"
        company_currency = self.env['res.currency'].search([('company_id',
                                                             '!=', False)])
        for company in self:
            company.multi_company_currency_enable = \
                1 if company_currency else 0

    @api.one
    def button_refresh_currency(self):
        """Refresh the currencies rates !!for all companies now"""
        self.services_to_use.refresh_currency()

    _inherit = "res.company"

    # Activate the currency update
    auto_currency_up = fields.Boolean(
        string='Automatic Update',
        help="Automatic update of the currencies for this company")
    # Function field that allows to know the
    # multi company currency implementation
    multi_company_currency_enable = fields.Boolean(
        string='Multi company currency', translate=True,
        compute="_compute_multi_curr_enable",
        help="When this option is unchecked it will allow users "
             "to set a distinct currency updates on each company."
        )
    # List of services to fetch rates
    services_to_use = fields.One2many(
        'currency.rate.update.service',
        'company_id',
        string='Currency update services')
