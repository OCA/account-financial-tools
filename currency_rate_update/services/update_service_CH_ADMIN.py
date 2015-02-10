# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
#
#    Abstract class to fetch rates from Swiss Federal Authorities
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
from .currency_getter_interface import Currency_getter_interface
import logging
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class CH_ADMIN_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for Admin.ch service.
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
            "Supported currencies = " + str(self.supported_currency_array)
        )
        self.validate_cur(main_currency)
        if main_currency != 'CHF':
            main_curr_data = self.rate_retrieve(dom, adminch_ns, main_currency)
            # 1 MAIN_CURRENCY = main_rate CHF
            rate_curr = main_curr_data['rate_currency']
            rate_ref = main_curr_data['rate_ref']
            main_rate = rate_curr / rate_ref
        for curr in currency_array:
            self.validate_cur(curr)
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
