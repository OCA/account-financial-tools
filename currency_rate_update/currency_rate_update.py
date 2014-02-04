# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 Camptocamp SA
#    @author Nicolas Bessi
#    @source JBA and AWST inpiration
#    @contributor Grzegorz Grzelak (grzegorz.grzelak@birdglobe.com), Joel Grand-Guillaume
#    Copyright (c) 2010 Alexis de Lattre (alexis@via.ecp.fr)
#     - ported XML-based webservices (Admin.ch, ECB, PL NBP) to new XML lib
#     - rates given by ECB webservice is now correct even when main_cur <> EUR
#     - rates given by PL_NBP webservice is now correct even when main_cur <> PLN
#     - if company_currency <> CHF, you can now update CHF via Admin.ch webservice
#       (same for EUR with ECB webservice and PLN with NBP webservice)
#     For more details, see Launchpad bug #645263
#     - mecanism to check if rates given by the webservice are "fresh" enough to be
#       written in OpenERP ('max_delta_days' parameter for each currency update service)
#        Ported to OpenERP 7.0 by Lorenzo Battistini <lorenzo.battistini@agilebg.com>
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

# TODO "nice to have" : restain the list of currencies that can be added for
# a webservice to the list of currencies supported by the Webservice
# TODO : implement max_delta_days for Yahoo webservice

from openerp.osv import fields, osv, orm
import time
from datetime import datetime, timedelta
import logging
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class Currency_rate_update_service(osv.Model):
    """Class thats tell for wich services wich currencies
    have to be updated"""
    _name = "currency.rate.update.service"
    _description = "Currency Rate Update"
    _columns = {
                    ##list of webservicies the value sould be a class name
                    'service' : fields.selection(
                                                    [
                                                    ('Admin_ch_getter','Admin.ch'),
                                                    ('ECB_getter','European Central Bank'),
                                                    #('NYFB_getter','Federal Reserve Bank of NY'),
                                                    #('Google_getter','Google Finance'),
                                                    ('Yahoo_getter','Yahoo Finance '),
                                                    ('PL_NBP_getter','Narodowy Bank Polski'),  # Added for polish rates
                                                    ('Banxico_getter', 'Banco de México'),  # Added for mexican rates
                                                    # Bank of Canada is using RSS-CB http://www.cbwiki.net/wiki/index.php/Specification_1.1 :
                                                    # This RSS format is used by other national banks (Thailand, Malaysia, Mexico...)
                                                    ('CA_BOC_getter','Bank of Canada - noon rates'),  # Added for canadian rates
                                                    ],
                                                    "Webservice to use",
                                                    required = True
                                                ),
                     ##list of currency to update
                    'currency_to_update' : fields.many2many(
                                                            'res.currency',
                                                            'res_curreny_auto_udate_rel',
                                                            'service_id',
                                                            'currency_id',
                                                            'currency to update with this service',
                                                            ),
                    #back ref
                    'company_id' : fields.many2one(
                                                    'res.company',
                                                    'linked company',
                                                    ),
                    ##note fileds that will be used as a logger
                    'note':fields.text('update notice'),
                    'max_delta_days': fields.integer('Max delta days', required=True, help="If the time delta between the rate date given by the webservice and the current date exeeds this value, then the currency rate is not updated in OpenERP."),
                }
    _defaults = {
            'max_delta_days': lambda *a: 4,
    }
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
        (_check_max_delta_days, "'Max delta days' must be >= 0", ['max_delta_days']),
    ]


class Currency_rate_update(osv.Model):
    """Class that handle an ir cron call who will
    update currencies based on a web url"""
    _name = "currency.rate.update"
    _description = "Currency Rate Update"
    ##dict that represent a cron object
    cron = {
            'active'          : False,
            'priority'        : 1,
            'interval_number' : 1,
            'interval_type'   : 'weeks',
            'nextcall'        : time.strftime("%Y-%m-%d %H:%M:%S", (datetime.today() + timedelta(days=1)).timetuple() ), #tomorrow same time
            'numbercall'      : -1,
            'doall'           : True,
            'model'           : 'currency.rate.update',
            'function'        : 'run_currency_update',
            'args'            : '()',
    }

    LOG_NAME = 'cron-rates'
    MOD_NAME = 'currency_rate_update: '
    def get_cron_id(self, cr, uid, context):
        """return the updater cron's id. Create one if the cron does not exists """

        cron_id = 0
        cron_obj = self.pool.get('ir.cron')
        try:
            #find the cron that send messages
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
        except Exception,e :
            _logger.info('warning cron not found one will be created')
            pass # ignore if the cron is missing cause we are going to create it in db

        #the cron does not exists
        if not cron_id :
            #translate
            self.cron['name'] = _('Currency Rate Update')
            cron_id = cron_obj.create(cr, uid, self.cron, context)

        return cron_id

    def save_cron(self, cr, uid, datas, context={}):
        """save the cron config data should be a dict"""
        #modify the cron
        cron_id = self.get_cron_id(cr, uid, context)
        result = self.pool.get('ir.cron').write(cr, uid, [cron_id], datas)

    def run_currency_update(self, cr, uid):
        "update currency at the given frequence"
        factory = Currency_getter_factory()
        curr_obj = self.pool.get('res.currency')
        rate_obj = self.pool.get('res.currency.rate')
        companies = self.pool.get('res.company').search(cr, uid, [])
        for comp in self.pool.get('res.company').browse(cr, uid, companies):
            ##the multi company currency can beset or no so we handle
            ##the two case
            if not comp.auto_currency_up :
                continue
            #we initialise the multi compnay search filter or not serach filter
            search_filter = []
            if comp.multi_company_currency_enable :
                search_filter = [('company_id','=',comp.id)]
            #we fetch the main currency looking for currency with base = true. The main rate should be set at  1.00
            main_curr_ids = curr_obj.search(cr, uid, [('base','=',True),('company_id','=',comp.id)])
            if not main_curr_ids:
                # If we can not find a base currency for this company we look for one with no company set
                main_curr_ids = curr_obj.search(cr, uid, [('base','=',True),('company_id','=', False)])
            if main_curr_ids:
                main_curr_rec = curr_obj.browse(cr, uid, main_curr_ids[0])
            else:
                raise orm.except_orm(_('Error!'),('There is no base currency set!'))
            if main_curr_rec.rate != 1:
                raise orm.except_orm(_('Error!'),('Base currency rate should be 1.00!'))
            main_curr = main_curr_rec.name
            for service in comp.services_to_use :
                print "comp.services_to_use =", comp.services_to_use
                note = service.note or ''
                try :
                    ## we initalize the class that will handle the request
                    ## and return a dict of rate
                    getter = factory.register(service.service)
                    print "getter =", getter
                    curr_to_fetch = map(lambda x : x.name, service.currency_to_update)
                    res, log_info = getter.get_updated_currency(curr_to_fetch, main_curr, service.max_delta_days)
                    rate_name = time.strftime('%Y-%m-%d')
                    for curr in service.currency_to_update :
                        if curr.name == main_curr :
                            continue
                        do_create = True
                        for rate in curr.rate_ids :
                            if rate.name == rate_name :
                                rate.write({'rate':res[curr.name]})
                                do_create = False
                                break
                        if do_create :
                            vals = {
                                        'currency_id': curr.id,
                                        'rate':res[curr.name],
                                        'name': rate_name
                                    }
                            rate_obj.create(
                                            cr,
                                            uid,
                                            vals,
                                        )

                    # show the most recent note at the top
                    note = "\n%s currency updated. "\
                       %(datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S'))\
                       + note
                    note = (log_info or '') + note
                    service.write({'note':note})
                except Exception, e:
                    error_msg = "\n%s ERROR : %s"\
                        %(datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S'), str(e))\
                        + note
                    _logger.info(str(e))
                    service.write({'note':error_msg})



### Error Definition as specified in python 2.6 PEP
class AbstractClassError(Exception):
    def __str__(self):
        return 'Abstract Class'
    def __repr__(self):
     return 'Abstract Class'

class AbstractMethodError(Exception):
    def __str__(self):
        return 'Abstract Method'
    def __repr__(self):
        return 'Abstract Method'

class UnknowClassError(Exception):
    def __str__(self):
        return 'Unknown Class'
    def __repr__(self):
        return 'Unknown Class'
class UnsuportedCurrencyError(Exception):
    def __init__(self, value):
           self.curr = value
    def __str__(self):
        return 'Unsupported currency '+self.curr
    def __repr__(self):
        return 'Unsupported currency '+self.curr

### end of error definition
class Currency_getter_factory():
    """Factory pattern class that will return
    a currency getter class base on the name passed
    to the register method"""
    def register(self, class_name):
        allowed = [
                          'Admin_ch_getter',
                          'PL_NBP_getter',
                          'ECB_getter',
                          'NYFB_getter',
                          'Google_getter',
                          'Yahoo_getter',
                          'Banxico_getter',
                          'CA_BOC_getter',
                    ]
        if class_name in allowed:
            class_def = eval(class_name)
            return class_def()
        else :
            raise UnknowClassError


class Curreny_getter_interface(object) :
    "Abstract class of currency getter"

    #remove in order to have a dryer code
    # def __init__(self):
    #    raise AbstractClassError

    log_info = " "

    supported_currency_array = \
['AFN', 'ALL', 'DZD', 'USD', 'USD', 'USD', 'EUR', 'AOA', 'XCD', 'XCD', 'ARS',
'AMD', 'AWG', 'AUD', 'EUR', 'AZN', 'EUR', 'BSD', 'BHD', 'EUR', 'BDT', 'BBD',
'XCD', 'BYR', 'EUR', 'BZD', 'XOF', 'BMD', 'BTN', 'INR', 'BOB', 'ANG', 'BAM',
'BWP', 'NOK', 'BRL', 'GBP', 'USD', 'USD', 'BND', 'BGN', 'XOF', 'MMK', 'BIF',
'XOF', 'USD', 'KHR', 'XAF', 'CAD', 'EUR', 'CVE', 'KYD', 'XAF', 'XAF', 'CLP',
'CNY', 'AUD', 'AUD', 'COP', 'XAF', 'KMF', 'XPF', 'XAF', 'CDF', 'NZD', 'CRC',
'HRK', 'CUP', 'ANG', 'EUR', 'CYP', 'CZK', 'DKK', 'DJF', 'XCD', 'DOP', 'EUR',
'XCD', 'IDR', 'USD', 'EGP', 'EUR', 'SVC', 'USD', 'GBP', 'XAF', 'ETB', 'ERN',
'EEK', 'ETB', 'EUR', 'FKP', 'DKK', 'FJD', 'EUR', 'EUR', 'EUR', 'XPF', 'XPF',
'EUR', 'XPF', 'XAF', 'GMD', 'GEL', 'EUR', 'GHS', 'GIP', 'XAU', 'GBP', 'EUR',
'DKK', 'XCD', 'XCD', 'EUR', 'USD', 'GTQ', 'GGP', 'GNF', 'XOF', 'GYD', 'HTG',
'USD', 'AUD', 'BAM', 'EUR', 'EUR', 'HNL', 'HKD', 'HUF', 'ISK', 'INR', 'IDR',
'XDR', 'IRR', 'IQD', 'EUR', 'IMP', 'ILS', 'EUR', 'JMD', 'NOK', 'JPY', 'JEP',
'JOD', 'KZT', 'AUD', 'KES', 'AUD', 'KPW', 'KRW', 'KWD', 'KGS', 'LAK', 'LVL',
'LBP', 'LSL', 'ZAR', 'LRD', 'LYD', 'CHF', 'LTL', 'EUR', 'MOP', 'MKD', 'MGA',
'EUR', 'MWK', 'MYR', 'MVR', 'XOF', 'EUR', 'MTL', 'FKP', 'USD', 'USD', 'EUR',
'MRO', 'MUR', 'EUR', 'AUD', 'MXN', 'USD', 'USD', 'EUR', 'MDL', 'EUR', 'MNT',
'EUR', 'XCD', 'MAD', 'MZN', 'MMK', 'NAD', 'ZAR', 'AUD', 'NPR', 'ANG', 'EUR',
'XCD', 'XPF', 'NZD', 'NIO', 'XOF', 'NGN', 'NZD', 'AUD', 'USD', 'NOK', 'OMR',
'PKR', 'USD', 'XPD', 'PAB', 'USD', 'PGK', 'PYG', 'PEN', 'PHP', 'NZD', 'XPT',
'PLN', 'EUR', 'STD', 'USD', 'QAR', 'EUR', 'RON', 'RUB', 'RWF', 'STD', 'ANG',
'MAD', 'XCD', 'SHP', 'XCD', 'XCD', 'EUR', 'XCD', 'EUR', 'USD', 'WST', 'EUR',
'SAR', 'SPL', 'XOF', 'RSD', 'SCR', 'SLL', 'XAG', 'SGD', 'ANG', 'ANG', 'EUR',
'EUR', 'SBD', 'SOS', 'ZAR', 'GBP', 'GBP', 'EUR', 'XDR', 'LKR', 'SDG', 'SRD',
'NOK', 'SZL', 'SEK', 'CHF', 'SYP', 'TWD', 'RUB', 'TJS', 'TZS', 'THB', 'IDR',
'TTD', 'XOF', 'NZD', 'TOP', 'TTD', 'TND', 'TRY', 'TMM', 'USD', 'TVD', 'UGX',
'UAH', 'AED', 'GBP', 'USD', 'USD', 'UYU', 'USD', 'UZS', 'VUV', 'EUR', 'VEB',
'VEF', 'VND', 'USD', 'USD', 'USD', 'XPF', 'MAD', 'YER', 'ZMK', 'ZWD']

    ##updated currency this arry will contain the final result
    updated_currency = {}

    def get_updated_currency(self, currency_array, main_currency, max_delta_days) :
        """Interface method that will retrieve the currency
           This function has to be reinplemented in child"""
        raise AbstractMethodError

    def validate_cur(self, currency) :
        """Validate if the currency to update is supported"""
        if currency not in self.supported_currency_array :
            raise UnsuportedCurrencyError(currency)

    def get_url(self, url):
        """Return a string of a get url query"""
        try:
            import urllib
            objfile = urllib.urlopen(url)
            rawfile = objfile.read()
            objfile.close()
            return rawfile
        except ImportError:
            raise osv.except_osv('Error !', self.MOD_NAME+'Unable to import urllib !')
        except IOError:
            raise osv.except_osv('Error !', self.MOD_NAME+'Web Service does not exist !')

    def check_rate_date(self, rate_date, max_delta_days):
        """Check date constrains. WARN : rate_date must be of datetime type"""
        days_delta = (datetime.today() - rate_date).days
        if days_delta > max_delta_days:
            raise Exception('The rate timestamp (%s) is %d days away from today, which is over the limit (%d days). Rate not updated in OpenERP.'%(rate_date, days_delta, max_delta_days))
        # We always have a warning when rate_date <> today
        rate_date_str = datetime.strftime(rate_date, '%Y-%m-%d')
        if rate_date_str != datetime.strftime(datetime.today(), '%Y-%m-%d'):
            self.log_info = "WARNING : the rate timestamp (%s) is not today's date" % rate_date_str
            _logger.warning("the rate timestamp (%s) is not today's date", rate_date_str)


#Yahoo ###################################################################################
class Yahoo_getter(Curreny_getter_interface) :
    """Implementation of Currency_getter_factory interface
    for Yahoo finance service"""

    def get_updated_currency(self, currency_array, main_currency, max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        self.validate_cur(main_currency)
        url='http://download.finance.yahoo.com/d/quotes.txt?s="%s"=X&f=sl1c1abg'
        if main_currency in currency_array :
            currency_array.remove(main_currency)
        for curr in currency_array :
            self.validate_cur(curr)
            res = self.get_url(url%(main_currency+curr))
            val = res.split(',')[1]
            if val :
                self.updated_currency[curr] = val
            else :
                raise Exception('Could not update the %s'%(curr))

        return self.updated_currency, self.log_info  # empty string added by polish changes
##Admin CH ############################################################################
class Admin_ch_getter(Curreny_getter_interface) :
    """Implementation of Currency_getter_factory interface
    for Admin.ch service"""

    def rate_retrieve(self, dom, ns, curr) :
        """ Parse a dom node to retrieve-
        currencies data"""
        res = {}
        xpath_rate_currency = "/def:wechselkurse/def:devise[@code='%s']/def:kurs/text()"%(curr.lower())
        xpath_rate_ref = "/def:wechselkurse/def:devise[@code='%s']/def:waehrung/text()"%(curr.lower())
        res['rate_currency'] = float(dom.xpath(xpath_rate_currency, namespaces=ns)[0])
        res['rate_ref'] = float((dom.xpath(xpath_rate_ref, namespaces=ns)[0]).split(' ')[0])
        return res

    def get_updated_currency(self, currency_array, main_currency, max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        url='http://www.afd.admin.ch/publicdb/newdb/mwst_kurse/wechselkurse.php'
        #we do not want to update the main currency
        if main_currency in currency_array :
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("Admin.ch currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        _logger.debug("Admin.ch sent a valid XML file")
        adminch_ns = {'def': 'http://www.afd.admin.ch/publicdb/newdb/mwst_kurse'}
        rate_date = dom.xpath('/def:wechselkurse/def:datum/text()', namespaces=adminch_ns)[0]
        rate_date_datetime = datetime.strptime(rate_date, '%Y-%m-%d')
        self.check_rate_date(rate_date_datetime, max_delta_days)
        #we dynamically update supported currencies
        self.supported_currency_array = dom.xpath("/def:wechselkurse/def:devise/@code", namespaces=adminch_ns)
        self.supported_currency_array = [x.upper() for x in self.supported_currency_array]
        self.supported_currency_array.append('CHF')

        _logger.debug("Supported currencies = " + str(self.supported_currency_array))
        self.validate_cur(main_currency)
        if main_currency != 'CHF':
            main_curr_data = self.rate_retrieve(dom, adminch_ns, main_currency)
            # 1 MAIN_CURRENCY = main_rate CHF
            main_rate = main_curr_data['rate_currency'] / main_curr_data['rate_ref']
        for curr in currency_array :
            self.validate_cur(curr)
            if curr == 'CHF':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve(dom, adminch_ns, curr)
                # 1 MAIN_CURRENCY = rate CURR
                if main_currency == 'CHF' :
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else :
                    rate = main_rate * curr_data['rate_ref'] / curr_data['rate_currency']
            self.updated_currency[curr] = rate
            _logger.debug("Rate retrieved : 1 " + main_currency + ' = ' + str(rate) + ' ' + curr)
        return self.updated_currency, self.log_info

## ECB getter ############################################################################

class ECB_getter(Curreny_getter_interface) :
    """Implementation of Currency_getter_factory interface
    for ECB service"""

    def rate_retrieve(self, dom, ns, curr) :
        """ Parse a dom node to retrieve-
        currencies data"""
        res = {}
        xpath_curr_rate = "/gesmes:Envelope/def:Cube/def:Cube/def:Cube[@currency='%s']/@rate"%(curr.upper())
        res['rate_currency'] = float(dom.xpath(xpath_curr_rate, namespaces=ns)[0])
        return res

    def get_updated_currency(self, currency_array, main_currency, max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        url='http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
        # Important : as explained on the ECB web site, the currencies are
        # at the beginning of the afternoon ; so, until 3 p.m. Paris time
        # the currency rates are the ones of trading day N-1
        # see http://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html

        #we do not want to update the main currency
        if main_currency in currency_array :
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("ECB currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        _logger.debug("ECB sent a valid XML file")
        ecb_ns = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01', 'def': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        rate_date = dom.xpath('/gesmes:Envelope/def:Cube/def:Cube/@time', namespaces=ecb_ns)[0]
        rate_date_datetime = datetime.strptime(rate_date, '%Y-%m-%d')
        self.check_rate_date(rate_date_datetime, max_delta_days)
        #we dynamically update supported currencies
        self.supported_currency_array = dom.xpath("/gesmes:Envelope/def:Cube/def:Cube/def:Cube/@currency", namespaces=ecb_ns)
        self.supported_currency_array.append('EUR')
        _logger.debug("Supported currencies = " + str(self.supported_currency_array))
        self.validate_cur(main_currency)
        if main_currency != 'EUR':
            main_curr_data = self.rate_retrieve(dom, ecb_ns, main_currency)
        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'EUR':
                rate = 1 / main_curr_data['rate_currency']
            else:
                curr_data = self.rate_retrieve(dom, ecb_ns, curr)
                if main_currency == 'EUR':
                    rate = curr_data['rate_currency']
                else:
                    rate = curr_data['rate_currency'] / main_curr_data['rate_currency']
            self.updated_currency[curr] = rate
            _logger.debug("Rate retrieved : 1 " + main_currency + ' = ' + str(rate) + ' ' + curr)
        return self.updated_currency, self.log_info

##PL NBP ############################################################################
class PL_NBP_getter(Curreny_getter_interface) :   # class added according to polish needs = based on class Admin_ch_getter
    """Implementation of Currency_getter_factory interface
    for PL NBP service"""

    def rate_retrieve(self, dom, ns, curr) :
        """ Parse a dom node to retrieve
        currencies data"""
        res = {}
        xpath_rate_currency = "/tabela_kursow/pozycja[kod_waluty='%s']/kurs_sredni/text()"%(curr.upper())
        xpath_rate_ref = "/tabela_kursow/pozycja[kod_waluty='%s']/przelicznik/text()"%(curr.upper())
        res['rate_currency'] = float(dom.xpath(xpath_rate_currency, namespaces=ns)[0].replace(',','.'))
        res['rate_ref'] = float(dom.xpath(xpath_rate_ref, namespaces=ns)[0])
        return res

    def get_updated_currency(self, currency_array, main_currency, max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        url='http://www.nbp.pl/kursy/xml/LastA.xml'    # LastA.xml is always the most recent one
        #we do not want to update the main currency
        if main_currency in currency_array :
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("NBP.pl currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile) # If rawfile is not XML, it crashes here
        ns = {} # Cool, there are no namespaces !
        _logger.debug("NBP.pl sent a valid XML file")
        #node = xpath.Evaluate("/tabela_kursow", dom) # BEGIN Polish - rates table name
        #if isinstance(node, list) :
        #    node = node[0]
        #self.log_info = node.getElementsByTagName('numer_tabeli')[0].childNodes[0].data
        #self.log_info = self.log_info + " " + node.getElementsByTagName('data_publikacji')[0].childNodes[0].data    # END Polish - rates table name

        rate_date = dom.xpath('/tabela_kursow/data_publikacji/text()', namespaces=ns)[0]
        rate_date_datetime = datetime.strptime(rate_date, '%Y-%m-%d')
        self.check_rate_date(rate_date_datetime, max_delta_days)
        #we dynamically update supported currencies
        self.supported_currency_array = dom.xpath('/tabela_kursow/pozycja/kod_waluty/text()', namespaces=ns)
        self.supported_currency_array.append('PLN')
        _logger.debug("Supported currencies = " + str(self.supported_currency_array))
        self.validate_cur(main_currency)
        if main_currency != 'PLN':
            main_curr_data = self.rate_retrieve(dom, ns, main_currency)
            # 1 MAIN_CURRENCY = main_rate PLN
            main_rate = main_curr_data['rate_currency'] / main_curr_data['rate_ref']
        for curr in currency_array :
            self.validate_cur(curr)
            if curr == 'PLN':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve(dom, ns, curr)
                # 1 MAIN_CURRENCY = rate CURR
                if main_currency == 'PLN':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = main_rate * curr_data['rate_ref'] / curr_data['rate_currency']
            self.updated_currency[curr] = rate
            _logger.debug("Rate retrieved : 1 " + main_currency + ' = ' + str(rate) + ' ' + curr)
        return self.updated_currency, self.log_info


##Banco de México ############################################################################
class Banxico_getter(Curreny_getter_interface) :  # class added for Mexico rates
    """Implementation of Currency_getter_factory interface
    for Banco de México service"""

    def rate_retrieve(self):
        """ Get currency exchange from Banxico.xml and proccess it
        TODO: Get correct data from xml instead of process string
        """
        url = 'http://www.banxico.org.mx/rsscb/rss?BMXC_canal=pagos&BMXC_idioma=es'

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


    def get_updated_currency(self, currency_array, main_currency, max_delta_days=1):
        """implementation of abstract method of Curreny_getter_interface"""
        logger = logging.getLogger(__name__)
        # we do not want to update the main currency
        if main_currency in currency_array :
            currency_array.remove(main_currency)

        # Suported currencies
        suported = ['MXN', 'USD']
        for curr in currency_array :
            if curr in suported:
                # Get currency data
                main_rate = self.rate_retrieve()
                if main_currency == 'MXN':
                    rate = 1 / main_rate
                else:
                    rate = main_rate
            else:
                """ No other currency supported
                """
                continue

            self.updated_currency[curr] = rate
            logger.debug("Rate retrieved : " + main_currency + ' = ' + str(rate) + ' ' + curr)


##CA BOC #####   Bank of Canada   ############################################################
class CA_BOC_getter(Curreny_getter_interface) :
    """Implementation of Curreny_getter_factory interface for Bank of Canada RSS service"""

    def get_updated_currency(self, currency_array, main_currency, max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""

        # as of Jan 2014 BOC is publishing noon rates for about 60 currencies
        url = 'http://www.bankofcanada.ca/stats/assets/rates_rss/noon/en_%s.xml'
        # closing rates are available as well (please note there are only 12
        # currencies reported):
        # http://www.bankofcanada.ca/stats/assets/rates_rss/closing/en_%s.xml

        #we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)

        import feedparser
        import pytz
        from dateutil import parser

        for curr in currency_array:

            _logger.debug("BOC currency rate service : connecting...")
            dom = feedparser.parse(url % curr)

            self.validate_cur(curr)

            # check if BOC service is running
            if dom.bozo and dom.status <> 404:
                _logger.error("Bank of Canada - service is down - try again\
                    later...")

            # check if BOC sent a valid response for this currency
            if dom.status != 200:
                _logger.error("Exchange data for %s is not reported by Bank\
                    of Canada." % curr)
                raise osv.except_osv('Error !', 'Exchange data for %s is not\
                    reported by Bank of Canada.' % str(curr))

            _logger.debug("BOC sent a valid RSS file for: " + curr)

            # check for valid exchange data
            if (dom.entries[0].cb_basecurrency == main_currency) and \
                    (dom.entries[0].cb_targetcurrency == curr):
                rate = dom.entries[0].cb_exchangerate.split('\n', 1)[0]
                rate_date_datetime = parser.parse(dom.entries[0].updated)\
                    .astimezone(pytz.utc).replace(tzinfo=None)
                self.check_rate_date(rate_date_datetime, max_delta_days)
                self.updated_currency[curr] = rate
                _logger.debug("BOC Rate retrieved : 1 " + main_currency +
                    ' = ' + str(rate) + ' ' + curr)
            else:
                _logger.error("Exchange data format error for Bank of Canada -\
                    %s. Please check provider data format and/or source code." % curr)
                raise osv.except_osv('Error !', 'Exchange data format error for\
                    Bank of Canada - %s !' % str(curr))

        return self.updated_currency, self.log_info
