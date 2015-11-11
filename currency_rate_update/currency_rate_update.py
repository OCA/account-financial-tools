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
#     - mechanism to check if rates given by the webservice are "fresh"
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
import time
import pytz
import dateutil
import feedparser
from datetime import datetime, timedelta

from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT,
    ustr,
)
from openerp.osv import fields, orm
from openerp.osv.osv import except_osv
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class CurrencyRateUpdateService(orm.Model):
    """Class that tells for which services which currencies have to be updated

    """
    _name = "currency.rate.update.service"
    _description = "Currency Rate Update"
    _columns = {
        # List of webservicies the value sould be a class name
        'service': fields.selection(
            [
                ('Admin_ch_getter', 'Admin.ch'),
                ('ECB_getter', 'European Central Bank'),
                ('Yahoo_getter', 'Yahoo Finance '),
                # Added for polish rates
                ('PL_NBP_getter', 'Narodowy Bank Polski'),
                # Added for mexican rates
                ('Banxico_getter', 'Banco de México'),
                # Bank of Canada is using RSS-CB
                # http://www.cbwiki.net/wiki/index.php/Specification_1.1
                # This RSS format is used by other national banks
                #  (Thailand, Malaysia, Mexico...)
                ('BankOfCanadaGetter', 'Bank of Canada - noon rates'),
            ],
            "Webservice to use",
            required=True
        ),
        # List of currency to update
        'currency_to_update': fields.many2many(
            'res.currency',
            'res_curreny_auto_udate_rel',
            'service_id',
            'currency_id',
            'currency to update with this service',
        ),
        # Back ref
        'company_id': fields.many2one(
            'res.company',
            'linked company',
        ),
        # Note fields that will be used as a logger
        'note': fields.text('update notice'),
        'max_delta_days': fields.integer(
            'Max delta days',
            required=True,
            help="If the time delta between the "
            "rate date given by the webservice and "
            "the current date exceeds this value, "
            "then the currency rate is not updated in OpenERP."
        ),
    }
    _defaults = {'max_delta_days': 4}
    _sql_constraints = [
        (
            'curr_service_unique',
            'unique (service, company_id)',
            _('You can use a service one time per company !')
        )
    ]

    def _check_max_delta_days(self, cr, uid, ids):
        for company in self.read(cr, uid, ids, ['max_delta_days']):
            if company['max_delta_days'] >= 0:
                continue
            else:
                return False
        return True

    _constraints = [
        (_check_max_delta_days,
         "'Max delta days' must be >= 0",
         ['max_delta_days']),
    ]


class CurrencyRateUpdate(orm.Model):
    """Class that handle an ir cron call who will
    update currencies based on a web url"""
    _name = "currency.rate.update"
    _description = "Currency Rate Update"
    # Dict that represent a cron object
    nextcall_time = datetime.today() + timedelta(days=1)
    nextcall = nextcall_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    cron = {
        'active': False,
        'priority': 1,
        'interval_number': 1,
        'interval_type': 'weeks',
        'nextcall': nextcall,
        'numbercall': -1,
        'doall': True,
        'model': 'currency.rate.update',
        'function': 'run_currency_update',
        'args': '()',
    }

    LOG_NAME = 'cron-rates'
    MOD_NAME = 'currency_rate_update: '

    def get_cron_id(self, cr, uid, context):
        """Returns the updater cron's id.
        Create one if the cron does not exists
        """

        cron_id = 0
        cron_obj = self.pool.get('ir.cron')
        try:
            # Finds the cron that send messages
            cron_id = cron_obj.search(
                cr,
                uid,
                [
                    ('function', 'ilike', self.cron['function']),
                    ('model', 'ilike', self.cron['model'])
                ],
                context={
                    'active_test': False
                }
            )
            cron_id = int(cron_id[0])
        except Exception:
            _logger.info('warning cron not found one will be created')
            # Ignore if the cron is missing cause we are
            # going to create it in db
            pass
        if not cron_id:
            self.cron['name'] = _('Currency Rate Update')
            cron_id = cron_obj.create(cr, uid, self.cron, context)
        return cron_id

    def save_cron(self, cr, uid, datas, context=None):
        """save the cron config data should be a dict"""
        cron_id = self.get_cron_id(cr, uid, context)
        return self.pool.get('ir.cron').write(cr, uid, [cron_id], datas)

    def run_currency_update(self, cr, uid, context=None):
        """Update currency at the given frequency"""
        curr_obj = self.pool.get('res.currency')
        rate_obj = self.pool.get('res.currency.rate')
        company_obj = self.pool.get('res.company')
        companies = company_obj.search(cr, uid, [], context=context)
        errors = []
        for comp in company_obj.browse(cr, uid, companies, context=context):
            # The multi company currency can beset or no so we handle
            # The two case
            if not comp.auto_currency_up:
                continue
            # We fetch the main currency looking for currency with base = true.
            # The main rate should be set at  1.00
            main_curr_ids = curr_obj.search(
                cr, uid,
                [('base', '=', True), ('company_id', '=', comp.id)],
                context=context
            )
            if not main_curr_ids:
                # If we can not find a base currency for this company
                # we look for one with no company set
                main_curr_ids = curr_obj.search(
                    cr, uid,
                    [('base', '=', True), ('company_id', '=', False)],
                    context=context
                )
            if main_curr_ids:
                main_curr_rec = curr_obj.browse(cr, uid, main_curr_ids[0])
            else:
                raise orm.except_orm(
                    _('Error!'),
                    _('There is no base currency set!')
                )
            if main_curr_rec.rate != 1:
                raise orm.except_orm(
                    _('Error'),
                    _('Base currency rate should be 1.00.\n'
                      'Currency %s has rate of %f')
                    % (main_curr_rec.name, main_curr_rec.rate)
                )
            main_curr = main_curr_rec.name
            for service in comp.services_to_use:
                note = service.note or ''
                try:
                    # We initialize the class that will handle the request
                    # and return a dict of rate
                    getter = register(service.service)
                    curr_to_fetch = map(lambda x: x.name,
                                        service.currency_to_update)
                    res, log_info = getter.get_updated_currency(
                        curr_to_fetch,
                        main_curr,
                        service.max_delta_days
                    )
                    rate_name = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
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
                            rate_obj.create(
                                cr,
                                uid,
                                vals,
                                context=context
                            )

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
                    if isinstance(exc, (orm.except_orm, except_osv)):
                        exc_repr = exc.value
                    else:
                        exc_repr = repr(exc)
                    error_msg = "\n%s ERROR : %s %s" % (
                        datetime.today().strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT
                        ),
                        exc_repr,
                        note
                    )
                    _logger.info(exc_repr)
                    service.write({'note': error_msg})
                    errors.append(error_msg)
        return errors


def register(class_name):
    allowed = [
        'Admin_ch_getter',
        'PL_NBP_getter',
        'ECB_getter',
        'NYFB_getter',
        'Google_getter',
        'Yahoo_getter',
        'Banxico_getter',
        'BankOfCanadaGetter',
    ]
    if class_name in allowed:
        class_def = eval(class_name)
        return class_def()
    else:
        raise AttributeError("Class %s not defined in module." % class_name)


class CurrencyGetterInterface(object):
    """Abstract class of currency getter"""

    log_info = " "

    supported_currency_array = [
        'AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN',
        'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BRL',
        'BSD', 'BTN', 'BWP', 'BYR', 'BZD', 'CAD', 'CDF', 'CHF', 'CLP', 'CNY',
        'COP', 'CRC', 'CUP', 'CVE', 'CYP', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD',
        'EEK', 'EGP', 'ERN', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL', 'GGP',
        'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK', 'HTG',
        'HUF', 'IDR', 'ILS', 'IMP', 'INR', 'IQD', 'IRR', 'ISK', 'JEP', 'JMD',
        'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD', 'KYD',
        'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LTL', 'LVL', 'LYD', 'MAD',
        'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRO', 'MTL', 'MUR', 'MVR',
        'MWK', 'MXN', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK', 'NPR', 'NZD',
        'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG', 'QAR', 'RON',
        'RSD', 'RUB', 'RWF', 'SAR', 'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP',
        'SLL', 'SOS', 'SPL', 'SRD', 'STD', 'SVC', 'SYP', 'SZL', 'THB', 'TJS',
        'TMM', 'TND', 'TOP', 'TRY', 'TTD', 'TVD', 'TWD', 'TZS', 'UAH', 'UGX',
        'USD', 'UYU', 'UZS', 'VEB', 'VEF', 'VND', 'VUV', 'WST', 'XAF', 'XAG',
        'XAU', 'XCD', 'XDR', 'XOF', 'XPD', 'XPF', 'XPT', 'YER', 'ZAR', 'ZMK',
        'ZWD'
    ]

    # Updated currency this array will contain the final result
    updated_currency = {}

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """Interface method that will retrieve the currency
           This function has to be reimplemented in child
        """
        raise NotImplementedError(
            "Function get_updated_currency not implemented in class %s"
            % self.__class__
        )

    def validate_currency(self, currency):
        """Validate if the currency to update is supported"""
        if currency not in self.supported_currency_array:
            raise AttributeError(
                'Unsupported currency %s' % currency
            )

    def get_url(self, url):
        """Return a string of a get url query"""
        try:
            import urllib
            objfile = urllib.urlopen(url)
            rawfile = objfile.read()
            objfile.close()
            return rawfile
        except ImportError:
            raise orm.except_orm(
                'Error !',
                self.MOD_NAME + 'Unable to import urllib !'
            )
        except IOError:
            raise orm.except_orm(
                'Error !',
                self.MOD_NAME + 'Web Service does not exist !'
            )

    def check_rate_date(self, rate_date, max_delta_days):
        """Check date constrains. rate_date must be of datetime type"""
        days_delta = (datetime.today() - rate_date).days
        if days_delta > max_delta_days:
            raise Exception(
                'The rate timestamp (%s) is %d days away from today, '
                'which is over the limit (%d days). '
                'Rate not updated in OpenERP.' % (rate_date,
                                                  days_delta,
                                                  max_delta_days)
            )

        # We always have a warning when rate_date != today
        rate_date_str = datetime.strftime(rate_date,
                                          DEFAULT_SERVER_DATE_FORMAT)
        if rate_date.date() != datetime.today().date():
            msg = "The rate timestamp (%s) is not today's date"
            self.log_info = "WARNING : %s %s" % (msg, rate_date_str)
            _logger.warning(msg, rate_date_str)


class YahooGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Yahoo finance service
    """

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_currency(main_currency)
        url = ('http://download.finance.yahoo.com/d/'
               'quotes.txt?s="%s"=X&f=sl1c1abg')
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        for curr in currency_array:
            self.validate_currency(curr)
            res = self.get_url(url % (main_currency + curr))
            val = res.split(',')[1]
            if val:
                self.updated_currency[curr] = val
            else:
                raise Exception('Could not update the %s' % (curr))

        return self.updated_currency, self.log_info


class Admin_ch_getter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Admin.ch service

    """

    def rate_retrieve(self, dom, ns, curr):
        """Parse a dom node to retrieve currencies data"""
        res = {}
        xpath_rate_currency = ("/def:wechselkurse/def:devise[@code='%s']/"
                               "def:kurs/text()") % (curr.lower())
        xpath_rate_ref = ("/def:wechselkurse/def:devise[@code='%s']/"
                          "def:waehrung/text()") % (curr.lower())
        res['rate_currency'] = float(
            dom.xpath(xpath_rate_currency, namespaces=ns)[0]
        )
        res['rate_ref'] = float(
            (dom.xpath(xpath_rate_ref, namespaces=ns)[0]).split(' ')[0]
        )
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """Implementation of abstract method of Curreny_getter_interface"""
        url = ('http://www.afd.admin.ch/publicdb/newdb/'
               'mwst_kurse/wechselkurse.php')
        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("Admin.ch currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        _logger.debug("Admin.ch sent a valid XML file")
        adminch_ns = {
            'def': 'http://www.afd.admin.ch/publicdb/newdb/mwst_kurse'
        }
        rate_date = dom.xpath(
            '/def:wechselkurse/def:datum/text()',
            namespaces=adminch_ns
        )
        rate_date = rate_date[0]
        rate_date_datetime = datetime.strptime(rate_date,
                                               DEFAULT_SERVER_DATE_FORMAT)
        self.check_rate_date(rate_date_datetime, max_delta_days)
        # we dynamically update supported currencies
        self.supported_currency_array = dom.xpath(
            "/def:wechselkurse/def:devise/@code",
            namespaces=adminch_ns
        )
        self.supported_currency_array = [x.upper() for x
                                         in self.supported_currency_array]
        self.supported_currency_array.append('CHF')

        _logger.debug(
            "Supported currencies = " + ustr(self.supported_currency_array)
        )
        self.validate_currency(main_currency)
        if main_currency != 'CHF':
            main_curr_data = self.rate_retrieve(dom, adminch_ns, main_currency)
            # 1 MAIN_CURRENCY = main_rate CHF
            rate_curr = main_curr_data['rate_currency']
            rate_ref = main_curr_data['rate_ref']
            main_rate = rate_curr / rate_ref
        for curr in currency_array:
            self.validate_currency(curr)
            if curr == 'CHF':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve(dom, adminch_ns, curr)
                # 1 MAIN_CURRENCY = rate CURR
                if main_currency == 'CHF':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = (main_rate * curr_data['rate_ref'] /
                            curr_data['rate_currency'])
            self.updated_currency[curr] = rate
            _logger.debug(
                "Rate retrieved : 1 %s = %s %s" % (main_currency, rate, curr)
            )
        return self.updated_currency, self.log_info


class ECB_getter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for ECB service
    """

    def rate_retrieve(self, dom, ns, curr):
        """Parse a dom node to retrieve-
        currencies data

        """
        res = {}
        xpath_curr_rate = ("/gesmes:Envelope/def:Cube/def:Cube/"
                           "def:Cube[@currency='%s']/@rate") % (curr.upper())
        res['rate_currency'] = float(
            dom.xpath(xpath_curr_rate, namespaces=ns)[0]
        )
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        url = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
        # Important : as explained on the ECB web site, the currencies are
        # at the beginning of the afternoon ; so, until 3 p.m. Paris time
        # the currency rates are the ones of trading day N-1
        # http://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html

        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("ECB currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        _logger.debug("ECB sent a valid XML file")
        ecb_ns = {
            'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
            'def': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'
        }
        rate_date = dom.xpath('/gesmes:Envelope/def:Cube/def:Cube/@time',
                              namespaces=ecb_ns)[0]
        rate_date_datetime = datetime.strptime(rate_date,
                                               DEFAULT_SERVER_DATE_FORMAT)
        self.check_rate_date(rate_date_datetime, max_delta_days)
        # We dynamically update supported currencies
        self.supported_currency_array = dom.xpath(
            "/gesmes:Envelope/def:Cube/def:Cube/def:Cube/@currency",
            namespaces=ecb_ns
        )
        self.supported_currency_array.append('EUR')
        _logger.debug("Supported currencies = %s " %
                      self.supported_currency_array)
        self.validate_currency(main_currency)
        if main_currency != 'EUR':
            main_curr_data = self.rate_retrieve(dom, ecb_ns, main_currency)
        for curr in currency_array:
            self.validate_currency(curr)
            if curr == 'EUR':
                rate = 1 / main_curr_data['rate_currency']
            else:
                curr_data = self.rate_retrieve(dom, ecb_ns, curr)
                if main_currency == 'EUR':
                    rate = curr_data['rate_currency']
                else:
                    rate = (curr_data['rate_currency'] /
                            main_curr_data['rate_currency'])
            self.updated_currency[curr] = rate
            _logger.debug(
                "Rate retrieved : 1 %s = %s %s" % (main_currency, rate, curr)
            )
        return self.updated_currency, self.log_info


class PL_NBP_getter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for PL NBP service

    """

    def rate_retrieve(self, dom, ns, curr):
        """ Parse a dom node to retrieve
        currencies data"""
        res = {}
        xpath_rate_currency = ("/tabela_kursow/pozycja[kod_waluty='%s']/"
                               "kurs_sredni/text()") % (curr.upper())
        xpath_rate_ref = ("/tabela_kursow/pozycja[kod_waluty='%s']/"
                          "przelicznik/text()") % (curr.upper())
        res['rate_currency'] = float(
            dom.xpath(xpath_rate_currency, namespaces=ns)[0].replace(',', '.')
        )
        res['rate_ref'] = float(dom.xpath(xpath_rate_ref, namespaces=ns)[0])
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        # LastA.xml is always the most recent one
        url = 'http://www.nbp.pl/kursy/xml/LastA.xml'
        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("NBP.pl currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        ns = {}  # Cool, there are no namespaces !
        _logger.debug("NBP.pl sent a valid XML file")
        rate_date = dom.xpath('/tabela_kursow/data_publikacji/text()',
                              namespaces=ns)[0]
        rate_date_datetime = datetime.strptime(rate_date,
                                               DEFAULT_SERVER_DATE_FORMAT)
        self.check_rate_date(rate_date_datetime, max_delta_days)
        # We dynamically update supported currencies
        self.supported_currency_array = dom.xpath(
            '/tabela_kursow/pozycja/kod_waluty/text()',
            namespaces=ns
        )
        self.supported_currency_array.append('PLN')
        _logger.debug("Supported currencies = %s" %
                      self.supported_currency_array)
        self.validate_currency(main_currency)
        if main_currency != 'PLN':
            main_curr_data = self.rate_retrieve(dom, ns, main_currency)
            # 1 MAIN_CURRENCY = main_rate PLN
            main_rate = (main_curr_data['rate_currency'] /
                         main_curr_data['rate_ref'])
        for curr in currency_array:
            self.validate_currency(curr)
            if curr == 'PLN':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve(dom, ns, curr)
                # 1 MAIN_CURRENCY = rate CURR
                if main_currency == 'PLN':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = (main_rate * curr_data['rate_ref'] /
                            curr_data['rate_currency'])
            self.updated_currency[curr] = rate
            _logger.debug("Rate retrieved : %s = %s %s" %
                          (main_currency, rate, curr))
        return self.updated_currency, self.log_info


class Banxico_getter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Banco de México service

    """

    def rate_retrieve(self):
        """ Get currency exchange from Banxico.xml and proccess it
        TODO: Get correct data from xml instead of process string
        """
        url = ('http://www.banxico.org.mx/rsscb/rss?'
               'BMXC_canal=pagos&BMXC_idioma=es')

        from xml.dom.minidom import parse
        from StringIO import StringIO

        logger = logging.getLogger(__name__)
        logger.debug("Banxico currency rate service : connecting...")
        rawfile = self.get_url(url)

        dom = parse(StringIO(rawfile))
        logger.debug("Banxico sent a valid XML file")

        value = dom.getElementsByTagName('cb:value')[0]
        rate = value.firstChild.nodeValue

        return float(rate)

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days=1):
        """implementation of abstract method of Curreny_getter_interface"""
        logger = logging.getLogger(__name__)
        # we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)

        # Suported currencies
        suported = ['MXN', 'USD']
        for curr in currency_array:
            if curr in suported:
                # Get currency data
                main_rate = self.rate_retrieve()
                if main_currency == 'MXN':
                    rate = 1 / main_rate
                else:
                    rate = main_rate
            else:
                # No other currency supported
                continue

            self.updated_currency[curr] = rate
            logger.debug("Rate retrieved : %s = %s %s" %
                         (main_currency, rate, curr))
        return self.updated_currency, self.log_info


class BankOfCanadaConnection(object):
    """Connection object for bankofcanada.ca"""
    url = 'http://www.bankofcanada.ca/stats/assets/rates_rss/noon/en_%s.xml'

    def __init__(self, currency):
        self.currency = currency

    def __enter__(self):
        """As of Jan 2014 BOC is publishing noon rates for about 60 currencies
        Closing rates are available as well (please note there are only 12
        currencies reported):
        http://www.bankofcanada.ca/stats/assets/rates_rss/closing/en_%s.xml
        """
        _logger.debug("BOC currency rate service: connecting...")
        self.dom = feedparser.parse(self.url % self.currency)

        # check if BOC service is running
        if self.dom.bozo and self.dom.status != 404:
            _logger.warn(
                "Bank of Canada - service is down - try again later..."
            )

        # check if BOC sent a valid response for this currency
        if self.dom.status != 200:
            _logger.warn(
                "Exchange data for %s is not reported by Bank of Canada."
                % self.currency
            )
            raise orm.except_orm(
                _('Error'),
                _('Exchange data for %s is not reported by Bank of '
                  'Canada.') % ustr(self.currency)
            )

        _logger.debug("BOC sent a valid RSS file for: " + self.currency)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def base_currency(self):
        return self.dom.entries[0].cb_basecurrency

    @property
    def target_currency(self):
        return self.dom.entries[0].cb_targetcurrency

    @property
    def exchange_rate(self):
        return self.dom.entries[0].cb_exchangerate.split("\n", 1)[0]

    @property
    def updated(self):
        return self.dom.entries[0].updated

    @property
    def date_time(self):
        parsed_datetime = dateutil.parser.parse(self.updated)
        return parsed_datetime.astimezone(pytz.utc).replace(tzinfo=None)


class BankOfCanadaGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Bank of Canada RSS service

    """

    def get_updated_currency(self, currencies, main_currency, max_delta_days):
        """Implementation of abstract method of Currency_getter_interface

        :param currencies: List of currency name
        :type currencies: list of unicode
        :param main_currency: Name of Company's currency
        :type main_currency: unicode
        :param max_delta_days: Maximum allowable days of unsync
        :type max_delta_days: int
        :return: Updated list of currencies and their rates and log
        :rtype: dict, str
        :raises: orm.except_orm when there is a format error
        """

        errors = []

        for currency in currencies:
            # We do not want to update the main currency
            if currency == main_currency:
                continue
            try:
                self.validate_currency(currency)
                with BankOfCanadaConnection(currency) as conn:

                    # check for valid exchange data
                    if (conn.base_currency == main_currency and
                            conn.target_currency.startswith(currency)):
                        self.check_rate_date(conn.date_time, max_delta_days)
                        self.updated_currency[currency] = conn.exchange_rate
                        _logger.debug(
                            "BOC Rate retrieved : %s = %s %s" %
                            (main_currency, conn.exchange_rate, currency)
                        )
                    else:
                        _logger.warn(
                            "Exchange data format error for Bank of Canada -"
                            "%s. Please check provider data format "
                            "and/or source code." % currency)
                        raise orm.except_orm(
                            _('Error'),
                            _('Exchange data format error for Bank of Canada'
                              ' - %s') % ustr(currency)
                        )
            except (orm.except_orm, except_osv) as e:
                errors.append(ustr(e.value))
            except Exception as e:
                errors.append(ustr(e))

        if errors:
            raise orm.except_orm(
                _("Errors occurred during update"),
                "\n".join(errors)
            )

        return self.updated_currency, self.log_info
