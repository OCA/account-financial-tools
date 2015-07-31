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

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api, _
from openerp import exceptions

from ..services.currency_getter import Currency_getter_factory

_logger = logging.getLogger(__name__)

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
}

supported_currency_array = [
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BRL",
    "BSD", "BTN", "BWP", "BYR", "BZD", "CAD", "CDF", "CHF", "CLP", "CNY",
    "COP", "CRC", "CUP", "CVE", "CYP", "CZK", "DJF", "DKK", "DOP", "DZD",
    "EEK", "EGP", "ERN", "ETB", "EUR", "FJD", "FKP", "GBP", "GEL", "GGP",
    "GHS", "GIP", "GMD", "GNF", "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG",
    "HUF", "IDR", "ILS", "IMP", "INR", "IQD", "IRR", "ISK", "JEP", "JMD",
    "JOD", "JPY", "KES", "KGS", "KHR", "KMF", "KPW", "KRW", "KWD", "KYD",
    "KZT", "LAK", "LBP", "LKR", "LRD", "LSL", "LTL", "LVL", "LYD", "MAD",
    "MDL", "MGA", "MKD", "MMK", "MNT", "MOP", "MRO", "MTL", "MUR", "MVR",
    "MWK", "MXN", "MYR", "MZN", "NAD", "NGN", "NIO", "NOK", "NPR", "NZD",
    "OMR", "PAB", "PEN", "PGK", "PHP", "PKR", "PLN", "PYG", "QAR", "RON",
    "RSD", "RUB", "RWF", "SAR", "SBD", "SCR", "SDG", "SEK", "SGD", "SHP",
    "SLL", "SOS", "SPL", "SRD", "STD", "SVC", "SYP", "SZL", "THB", "TJS",
    "TMM", "TND", "TOP", "TRY", "TTD", "TVD", "TWD", "TZS", "UAH", "UGX",
    "USD", "UYU", "UZS", "VEB", "VEF", "VND", "VUV", "WST", "XAF", "XAG",
    "XAU", "XCD", "XDR", "XOF", "XPD", "XPF", "XPT", "YER", "ZAR", "ZMK",
    "ZWD"
]

YAHOO_supported_currency_array = [
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BRL",
    "BSD", "BTN", "BWP", "BYR", "BZD", "CAD", "CDF", "CHF", "CLF", "CLP",
    "CNH", "CNY", "COP", "CRC", "CUP", "CVE", "CZK", "DJF", "DKK", "DOP",
    "DZD", "EGP", "ERN", "ETB", "EUR", "FJD", "FKP", "GBP", "GEL", "GHS",
    "GIP", "GMD", "GNF", "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG", "HUF",
    "IDR", "IEP", "ILS", "INR", "IQD", "IRR", "ISK", "JMD", "JOD", "JPY",
    "KES", "KGS", "KHR", "KMF", "KPW", "KRW", "KWD", "KYD", "KZT", "LAK",
    "LBP", "LKR", "LRD", "LSL", "LTL", "LVL", "LYD", "MAD", "MDL", "MGA",
    "MKD", "MMK", "MNT", "MOP", "MRO", "MUR", "MVR", "MWK", "MXN", "MXV",
    "MYR", "MZN", "NAD", "NGN", "NIO", "NOK", "NPR", "NZD", "OMR", "PAB",
    "PEN", "PGK", "PHP", "PKR", "PLN", "PYG", "QAR", "RON", "RSD", "RUB",
    "RWF", "SAR", "SBD", "SCR", "SDG", "SEK", "SGD", "SHP", "SLL", "SOS",
    "SRD", "STD", "SVC", "SYP", "SZL", "THB", "TJS", "TMT", "TND", "TOP",
    "TRY", "TTD", "TWD", "TZS", "UAH", "UGX", "USD", "UYU", "UZS", "VEF",
    "VND", "VUV", "WST", "XAF", "XAG", "XAU", "XCD", "XCP", "XDR", "XOF",
    "XPD", "XPF", "XPT", "YER", "ZAR", "ZMW", "ZWL"]

RO_BNR_supported_currency_array = [
    "AED", "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EGP",
    "EUR", "GBP", "HUF", "INR", "JPY", "KRW", "MDL", "MXN", "NOK", "NZD",
    "PLN", "RON", "RSD", "RUB", "SEK", "TRY", "UAH", "USD", "XAU", "XDR",
    "ZAR"]

CA_BOC_supported_currency_array = [
    "AED", "ANG", "ARS", "AUD", "BOC", "BRL", "BSD", "CHF", "CLP", "CNY",
    "COP", "CZK", "DKK", "EUR", "FJD", "GBP", "GHS", "GTQ", "HKD", "HNL",
    "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JMD", "JPY", "KRW", "LKR",
    "MAD", "MMK", "MXN", "MYR", "NOK", "NZD", "PAB", "PEN", "PHP", "PKR",
    "PLN", "RON", "RSD", "RUB", "SEK", "SGD", "THB", "TND", "TRY", "TTD",
    "TWD", "USD", "VEF", "VND", "XAF", "XCD", "XPF", "ZAR"]

CH_ADMIN_supported_currency_array = [
    "AED", "ALL", "ARS", "AUD", "AZN", "BAM", "BDT", "BGN", "BHD", "BRL",
    "CAD", "CHF", "CLP", "CNY", "COP", "CRC", "CZK", "DKK", "DOP", "EGP",
    "ETB", "EUR", "GBP", "GTQ", "HKD", "HNL", "HRK", "HUF", "IDR", "ILS",
    "INR", "ISK", "JPY", "KES", "KHR", "KRW", "KWD", "KYD", "KZT", "LBP",
    "LKR", "LTL", "LVL", "LYD", "MAD", "MUR", "MXN", "MYR", "NGN", "NOK",
    "NZD", "OMR", "PAB", "PEN", "PHP", "PKR", "PLN", "QAR", "RON", "RSD",
    "RUB", "SAR", "SEK", "SGD", "THB", "TND", "TRY", "TWD", "TZS", "UAH",
    "USD", "UYU", "VEF", "VND", "ZAR"]

ECB_supported_currency_array = [
    "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP",
    "HKD", "HRK", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", "LTL", "MXN",
    "MYR", "NOK", "NZD", "PHP", "PLN", "RON", "RUB", "SEK", "SGD", "THB",
    "TRY", "USD", "ZAR"]

MX_BdM_supported_currency_array = [
    "ARS", "AUD", "BBD", "BMD", "BOB", "BRL", "BSD", "BZD", "CAD", "CHF",
    "CLP", "CNH", "CNY", "COP", "CRC", "CUP", "CZK", "DKK", "DOP", "DZD",
    "EGP", "ESD", "EUR", "FJD", "GBP", "GTQ", "GYD", "HKD", "HNL", "HUF",
    "IDR", "ILS", "INR", "IQD", "JMD", "JPY", "KES", "KRW", "KWD", "MAD",
    "MYR", "NGN", "NIC", "NOK", "NZD", "PAB", "PEN", "PHP", "PLN", "PYG",
    "RON", "RUB", "SAR", "SEK", "SGD", "SVC", "THB", "TRY", "TTD", "TWD",
    "UAH", "USD", "USD", "UYP", "VEF", "VND", "ZAR"]

PL_NBP_supported_currency_array = [
    "AUD", "BGN", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR",
    "GBP", "HKD", "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW",
    "LTL", "MXN", "MYR", "NOK", "NZD", "PHP", "PLN", "RON", "RUB", "SEK",
    "SGD", "THB", "TRY", "UAH", "USD", "XDR", "ZAR"]

supported_currecies = {
    'YAHOO_getter': YAHOO_supported_currency_array,
    'ECB_getter': ECB_supported_currency_array,
    'RO_BNR_getter': RO_BNR_supported_currency_array,
    'CA_BOC_getter': CA_BOC_supported_currency_array,
    'CH_ADMIN_getter': CH_ADMIN_supported_currency_array,
    'MX_BdM_getter': MX_BdM_supported_currency_array,
    'PL_NBP_getter': PL_NBP_supported_currency_array,
    }


class Currency_rate_update_service(models.Model):
    """Class keep services and currencies that
    have to be updated"""
    _name = "currency.rate.update.service"
    _description = "Currency Rate Update"

    @api.one
    @api.constrains('max_delta_days')
    def _check_max_delta_days(self):
        if self.max_delta_days < 0:
            raise exceptions.Warning(_('Max delta days must be >= 0'))

    @api.one
    @api.constrains('interval_number')
    def _check_interval_number(self):
        if self.interval_number < 0:
            raise exceptions.Warning(_('Interval number must be >= 0'))

    @api.onchange('interval_number')
    def _onchange_interval_number(self):
        if self.interval_number == 0:
            self.note = '%s Service deactivated. Currencies will no longer ' \
                        'be updated. \n%s' % (fields.Datetime.now(),
                                              self.note and self.note or '')

    @api.onchange('service')
    def _onchange_service(self):
        currency_list = ''
        if self.service:
            currencies = []
            currency_list = supported_currency_array
            company_id = False
            if self.company_id.multi_company_currency_enable:
                company_id = self.company_id.id
            currency_list = supported_currecies[self.service]
            if company_id:
                currencies = self.env['res.currency'].search(
                    [('name', 'in', currency_list),
                     '|', ('company_id', '=', company_id),
                     ('company_id', '=', False)])
            else:
                currencies = self.env['res.currency'].search(
                    [('name', 'in', currency_list),
                     ('company_id', '=', False)])
            self.currency_list = [(6, 0, [curr.id for curr in currencies])]

    # List of webservicies the value sould be a class name
    service = fields.Selection(
        [('CH_ADMIN_getter', 'Admin.ch'),
         ('ECB_getter', 'European Central Bank'),
         ('YAHOO_getter', 'Yahoo Finance'),
         # Added for polish rates
         ('PL_NBP_getter', 'National Bank of Poland'),
         # Added for mexican rates
         ('MX_BdM_getter', 'Bank of Mexico'),
         # Bank of Canada is using RSS-CB
         # http://www.cbwiki.net/wiki/index.php/Specification_1.1
         # This RSS format is used by other national banks
         #  (Thailand, Malaysia, Mexico...)
         ('CA_BOC_getter', 'Bank of Canada - noon rates'),
         # Added for romanian rates
         ('RO_BNR_getter', 'National Bank of Romania')
         ],
        string="Webservice to use",
        required=True)
    # List of currencies available on webservice
    currency_list = fields.Many2many('res.currency',
                                     'res_currency_update_avail_rel',
                                     'service_id',
                                     'currency_id',
                                     string='Currencies available')
    # List of currency to update
    currency_to_update = fields.Many2many('res.currency',
                                          'res_currency_auto_update_rel',
                                          'service_id',
                                          'currency_id',
                                          string='Currencies to update with '
                                          'this service')
    # Link with company
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'currency.rate.update.service'))
    # Note fileds that will be used as a logger
    note = fields.Text('Update logs')
    max_delta_days = fields.Integer(
        string='Max delta days', default=4, required=True,
        help="If the time delta between the rate date given by the "
        "webservice and the current date exceeds this value, "
        "then the currency rate is not updated in OpenERP.")
    interval_type = fields.Selection([
        ('days', 'Day(s)'),
        ('weeks', 'Week(s)'),
        ('months', 'Month(s)')],
        string='Currency update frequency',
        default='days')
    interval_number = fields.Integer(string='Frequency', default=1)
    next_run = fields.Date(string='Next run on', default=fields.Date.today())

    _sql_constraints = [('curr_service_unique',
                         'unique (service, company_id)',
                         _('You can use a service only one time per '
                           'company !'))]

    @api.one
    def refresh_currency(self):
        """Refresh the currencies rates !!for all companies now"""
        _logger.info(
            'Starting to refresh currencies with service %s (company: %s)',
            self.service, self.company_id.name)
        factory = Currency_getter_factory()
        curr_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        company = self.company_id
        # The multi company currency can be set or no so we handle
        # The two case
        if company.auto_currency_up:
            main_currency = curr_obj.search(
                [('base', '=', True), ('company_id', '=', company.id)],
                limit=1)
            if not main_currency:
                # If we can not find a base currency for this company
                # we look for one with no company set
                main_currency = curr_obj.search(
                    [('base', '=', True), ('company_id', '=', False)],
                    limit=1)
            if not main_currency:
                raise exceptions.Warning(_('There is no base currency set!'))
            if main_currency.rate != 1:
                raise exceptions.Warning(_('Base currency rate should '
                                           'be 1.00!'))
            note = self.note or ''
            try:
                # We initalize the class that will handle the request
                # and return a dict of rate
                getter = factory.register(self.service)
                curr_to_fetch = map(lambda x: x.name,
                                    self.currency_to_update)
                res, log_info = getter.get_updated_currency(
                    curr_to_fetch,
                    main_currency.name,
                    self.max_delta_days
                    )
                rate_name = \
                    fields.Datetime.to_string(datetime.utcnow().replace(
                        hour=0, minute=0, second=0, microsecond=0))
                for curr in self.currency_to_update:
                    if curr.id == main_currency.id:
                        continue
                    do_create = True
                    for rate in curr.rate_ids:
                        if rate.name == rate_name:
                            rate.rate = res[curr.name]
                            do_create = False
                            break
                    if do_create:
                        vals = {
                            'currency_id': curr.id,
                            'rate': res[curr.name],
                            'name': rate_name
                        }
                        rate_obj.create(vals)
                        _logger.info(
                            'Updated currency %s via service %s',
                            curr.name, self.service)

                # Show the most recent note at the top
                msg = '%s \n%s currency updated. %s' % (
                    log_info or '',
                    fields.Datetime.to_string(datetime.today()),
                    note
                )
                self.write({'note': msg})
            except Exception as exc:
                error_msg = '\n%s ERROR : %s %s' % (
                    fields.Datetime.to_string(datetime.today()),
                    repr(exc),
                    note
                )
                _logger.error(repr(exc))
                self.write({'note': error_msg})
            if self._context.get('cron', False):
                midnight = time(0, 0)
                next_run = (datetime.combine(
                            fields.Date.from_string(self.next_run),
                            midnight) +
                            _intervalTypes[str(self.interval_type)]
                            (self.interval_number)).date()
                self.next_run = next_run

    @api.multi
    def run_currency_update(self):
        # Update currency at the given frequence
        services = self.search([('next_run', '=', fields.Date.today())])
        services.with_context(cron=True).refresh_currency()

    @api.model
    def _run_currency_update(self):
        _logger.info('Starting the currency rate update cron')
        self.run_currency_update()
        _logger.info('End of the currency rate update cron')
