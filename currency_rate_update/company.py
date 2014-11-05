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

import logging

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from currency_rate_update import Currency_getter_factory

_logger = logging.getLogger(__name__)

class res_company(models.Model):
    """override company to add currency update"""

    @api.multi
    def _compute_multi_curr_enable(self):
        "check if multi company currency is enabled"
        result = {}
        fields = self.env['res.currency'].search([('company_id', '<>', False)])
        for company in self:
            company.multi_company_currency_enable = \
                1 if fields else 0

    @api.one
    def button_refresh_currency(self):
        """Refresh the currencies rates !!for all companies now"""
        self.ensure_one()
        self.services_to_use.refresh_currency()        
    
    _inherit = "res.company"
    
    # Activate the currency update
    auto_currency_up = fields.Boolean(
        'Automatical update of the currency this company')
    # Function field that allows to know the
    # multi company currency implementation
    multi_company_currency_enable = fields.Boolean(string="Multi company currency",
            compute = _compute_multi_curr_enable,
            help="If this case is not check you can"
                 " not set currency is active on two company"
        )
    # List of services to fetch rates
    services_to_use = fields.One2many(
        'currency.rate.update.service',
        'company_id',
        'Currency update services')    
