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

import time
from datetime import datetime, timedelta

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
        self.run_currency_update()
    
    @api.multi
    def run_currency_update(self):
        "Update currency at the given frequence"
        factory = Currency_getter_factory()
        curr_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        companies = self.search([])
        for company in companies:
            # The multi company currency can be set or no so we handle
            # The two case
            if not company.auto_currency_up:
                continue
            # We fetch the main currency looking for currency with base = true.
            # The main rate should be set at  1.00
            main_curr_ids = curr_obj.search( \
                [('base', '=', True), ('company_id', '=', company.id)])
            if not main_curr_ids:
                # If we can not find a base currency for this company
                # we look for one with no company set
                main_curr_ids = curr_obj.search( \
                    [('base', '=', True), ('company_id', '=', False)])
            if main_curr_ids:
                main_curr_rec = main_curr_ids[0]
            else:
                raise Warning(_('There is no base currency set!'))
            if main_curr_rec.rate != 1:
                raise Warning(_('Base currency rate should be 1.00!'))
            main_curr = main_curr_rec.name
            for service in company.services_to_use:
                note = service.note or ''
                try:
                    # We initalize the class that will handle the request
                    # and return a dict of rate
                    getter = factory.register(service.service)
                    curr_to_fetch = map(lambda x: x.name,
                                        service.currency_to_update)
                    res, log_info = getter.get_updated_currency(
                        curr_to_fetch,
                        main_curr,
                        service.max_delta_days
                    )
                    rate_name = datetime.strftime( \
                        datetime.utcnow().replace(hour=0, minute=0,second=0, microsecond=0), \
                        DEFAULT_SERVER_DATETIME_FORMAT)
                    for curr in service.currency_to_update:
                        if curr.name == main_curr:
                            continue
                        do_create = True
                        for rate in curr.rate_ids:
                            if rate.name == rate_name:
                                rate.write({'rate': res[curr.name]})
                                do_create = False
                                break
                        if do_create:
                            vals = {
                                'currency_id': curr.id,
                                'rate': res[curr.name],
                                'name': rate_name
                            }
                            rate_obj.create(vals)

                    # Show the most recent note at the top
                    msg = "%s \n%s currency updated. %s" % (
                        log_info or '',
                        datetime.today().strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT
                        ),
                        note
                    )
                    service.write({'note': msg})
                except Exception as exc:
                    error_msg = "\n%s ERROR : %s %s" % (
                        datetime.today().strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT
                        ),
                        repr(exc),
                        note
                    )
                    _logger.info(repr(exc))
                    service.write({'note': error_msg})

    @api.model
    def _run_currency_update(self):
        #comp = self.browse(cr, uid, self.search(cr, uid, [], context=context), context=context)
        self.run_currency_update()
        
    _inherit = "res.company"
    
    # Activate the currency update
    auto_currency_up = fields.Boolean(
        'Automatical update of the currency this company')
    # List of services to fetch rates
    services_to_use = fields.One2many(
        'currency.rate.update.service',
        'company_id',
        'Currency update services')
    # Function field that allows to know the
    # multi company currency implementation
    multi_company_currency_enable = fields.Boolean(string="Multi company currency",
            compute = _compute_multi_curr_enable,
            help="If this case is not check you can"
                 " not set currency is active on two company"
        )
