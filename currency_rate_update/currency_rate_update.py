# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 Camptocamp SA
#    @source JBA and AWST inpiration
#    @contributor Grzegorz Grzelak (grzegorz.grzelak@birdglobe.com),
#                 Joel Grand-Guillaume
#    Copyright (c) 2010 Alexis de Lattre (alexis@via.ecp.fr)
#     - ported XML-based webservices (Admin.ch, ECB, PL NBP) to new XML lib
#     - rates given by ECB webservice is now correct even when main_cur <> EUR
#     - rates given by PL_NBP webs. is now correct even when main_cur <> PLN
#     - if company_currency <> CHF, you can now update CHF via Admin.ch
#       (same for EUR with ECB webservice and PLN with NBP webservice)
#     For more details, see Launchpad bug #645263
#     - mecanism to check if rates given by the webservice are "fresh"
#       enough to be written in OpenERP
#       ('max_delta_days' parameter for each currency update service)
#    Ported to OpenERP 7.0 by Lorenzo Battistini
#                             <lorenzo.battistini@agilebg.com>
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

# TODO "nice to have" : restrain the list of currencies that can be added for
# a webservice to the list of currencies supported by the Webservice
# TODO : implement max_delta_days for Yahoo webservice

import logging

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, fields, api, _
from openerp.exceptions import Warning

from currency_getter import Currency_getter_factory

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
}
_logger = logging.getLogger(__name__)

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


class Currency_rate_update_service(models.Model):
    """Class thats tell for wich services wich currencies
    have to be updated"""
    _name = "currency.rate.update.service"
    _description = "Currency Rate Update"

    @api.one
    @api.constrains('max_delta_days')
    def _check_max_delta_days(self):
        if self and self.max_delta_days < 0:
            raise Warning(_('Max delta days must be >= 0'))

    @api.one
    @api.constrains('interval_number')
    def _check_interval_number(self):
        if self and self.interval_number < 0:
            raise Warning(_('Interval number must be > 0'))
        if self and self.interval_number == 0:
            raise Warning(
                _('Interval number is zero, currencies will not be updated')
                )

    @api.onchange('service')
    def _onchange_service(self):
        currency_list = ''
        if self.service:
            currencies = []
            currency_list = supported_currency_array
            company_id = False
            if self.company_id.multi_company_currency_enable:
                company_id = self.company_id.id
            if self.service == 'RO_BNR_getter':
                currency_list = [
                    "AED", "AUD", "BGN", "BRL", "CAD", "CHF",
                    "CNY", "CZK", "DKK", "EGP", "EUR", "GBP", "HUF", "INR",
                    "JPY", "KRW", "MDL", "MXN", "NOK", "NZD", "PLN", "RSD",
                    "RUB", "SEK", "TRY", "UAH", "USD", "XAU", "XDR", "ZAR"
                ]
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
    service = fields.Selection([
                ('CH_ADMIN_getter', 'Admin.ch'),
                ('ECB_getter', 'European Central Bank'),
                ('YAHOO_getter', 'Yahoo Finance'),
                # Added for polish rates
                ('PL_NBP_getter', 'Narodowy Bank Polski'),
                # Added for mexican rates
                ('MX_BdM_getter', 'Banco de México'),
                # Bank of Canada is using RSS-CB
                # http://www.cbwiki.net/wiki/index.php/Specification_1.1
                # This RSS format is used by other national banks
                #  (Thailand, Malaysia, Mexico...)
                ('CA_BOC_getter', 'Bank of Canada - noon rates'),
                # Added for romanian rates
                ('RO_BNR_getter', 'National Bank of Romania')
                                ],
                                "Webservice to use",
                                required=True)
    # List of currencies available on webservice
    currency_list = fields.Many2many('res.currency',
                                     'res_currency_update_avail_rel',
                                     'service_id',
                                     'currency_id',
                                     'Currencies available')
    # List of currency to update
    currency_to_update = fields.Many2many(
                                     'res.currency',
                                     'res_currency_auto_update_rel',
                                     'service_id',
                                     'currency_id',
                                     'Currencies to update with this service')
    # Link with company
    company_id = fields.Many2one('res.company', 'Linked Company')
    # Note fileds that will be used as a logger
    note = fields.Text('Update notice')
    max_delta_days = fields.Integer('Max delta days',
        default=lambda *a: 4, required=True,
        help="If the time delta between the rate date given by the webservice "
        "and the current date exeeds this value, then the currency rate is not"
        " updated in OpenERP.")
    interval_type = fields.Selection([
        ('days', 'Day(s)'),
        ('weeks', 'Week(s)'),
        ('months', 'Month(s)')],
        string='Currency update frecvency',
        default='days')
    interval_number = fields.Integer('Frecvency', default=0)
    next_run = fields.Date('Next run on', default=fields.Date.today())

    _sql_constraints = [('curr_service_unique', 'unique (service, company_id)',
                       _('You can use a service only one time per company !'))]

    @api.one
    def refresh_currency(self):
        """Refresh the currencies rates !!for all companies now"""
        self.ensure_one()
        factory = Currency_getter_factory()
        curr_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        company = self.company_id
        # The multi company currency can be set or no so we handle
        # The two case
        # if not company.auto_currency_up:
        #    continue
        main_curr_ids = curr_obj.search(
            [('base', '=', True), ('company_id', '=', company.id)])
        if not main_curr_ids:
            # If we can not find a base currency for this company
            # we look for one with no company set
            main_curr_ids = curr_obj.search(
                [('base', '=', True), ('company_id', '=', False)])
        if main_curr_ids:
            main_curr_rec = main_curr_ids[0]
        else:
            raise Warning(_('There is no base currency set!'))
        if main_curr_rec.rate != 1:
            raise Warning(_('Base currency rate should be 1.00!'))
        main_curr = main_curr_rec.name
        note = self.note or ''
        try:
            # We initalize the class that will handle the request
            # and return a dict of rate
            getter = factory.register(self.service)
            curr_to_fetch = map(lambda x: x.name,
                self.currency_to_update)
            res, log_info = getter.get_updated_currency(
                curr_to_fetch,
                main_curr,
                self.max_delta_days
                )
            rate_name = datetime.strftime(
                datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0),
                DEFAULT_SERVER_DATETIME_FORMAT)
            for curr in self.currency_to_update:
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
            self.write({'note': msg})
            if self._context.get('cron', False):
                next_run = (datetime.combine(datetime.strptime(
                                self.next_run, DEFAULT_SERVER_DATE_FORMAT),
                                datetime.min.time()) +
                                _intervalTypes[str(self.interval_type)]
                                (self.interval_number)).date()
                self.write({'next_run': next_run})
        except Exception as exc:
            error_msg = "\n%s ERROR : %s %s" % (
                datetime.today().strftime(
                DEFAULT_SERVER_DATETIME_FORMAT
                ),
                repr(exc),
                note
            )
            _logger.info(repr(exc))
            self.write({'note': error_msg})

    @api.multi
    def run_currency_update(self):
        "Update currency at the given frequence"
        ctx = dict(self._context)
        current_date = datetime.utcnow().date()
        services = self.search([('next_run', '=', current_date)])
        ctx['cron'] = True
        for service in services:
            service.with_context(ctx).refresh_currency()

    @api.model
    def _run_currency_update(self):
        self.run_currency_update()
