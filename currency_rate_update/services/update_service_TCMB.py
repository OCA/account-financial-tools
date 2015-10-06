# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
#    @author Ahmet Altinisik <functions for Turkish National Bank> 
#    Abstract class to fetch rates from European Central Bank
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

from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)


class TCMB_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for TCMB service used ECB_getter class code as a base
    """

    def rate_retrieve(self, dom, ns, curr):
        """Parse a dom node to retrieve-
        currencies data

        """
        res = {}
        xpath_curr_rate = '/Tarih_Date/Currency[@Kod="%s"]/ForexBuying/text()' % (curr.upper())
        res['rate_currency'] = float(
            dom.xpath(xpath_curr_rate, namespaces=ns)[0]
        )
        return res
    
    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        url = 'http://www.tcmb.gov.tr/kurlar/today.xml'
        # Important : as explained on the TCMB web site, the currencies are
        # updated at 15:30 Istanbul time ; so, until 3:30 p.m. Istanbul time
        # the currency rates are the ones of trading day N-1
        # https://www.turkiye.gov.tr/doviz-kurlari

        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("TCMB currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        _logger.debug("TCMB sent a valid XML file")
        ecb_ns = {}
        rate_date = dom.xpath('/Tarih_Date/@Date')[0]
        rate_date_datetime = datetime.strptime(rate_date, '%m/%d/%Y')
        self.check_rate_date(rate_date_datetime, max_delta_days)
        # We dynamically update supported currencies
        self.supported_currency_array = dom.xpath('/Tarih_Date/Currency/@Kod')
        self.supported_currency_array.append('TRY')
        _logger.debug("Supported currencies = %s " %
                      self.supported_currency_array)
        self.validate_cur(main_currency)

        if main_currency != 'TRY':
            main_curr_data = self.rate_retrieve(dom, ecb_ns, main_currency)
        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'TRY':
                rate = main_curr_data['rate_currency']
            else:
                curr_data = self.rate_retrieve(dom, ecb_ns, curr)
                if main_currency == 'TRY':
                    rate = 1 / curr_data['rate_currency']
                else:
                    rate = (curr_data['rate_currency'] /
                            main_curr_data['rate_currency'])
            self.updated_currency[curr] = rate
            _logger.debug(
                "TCMB Rate retrieved : 1 %s = %s %s" %
                (main_currency, rate, curr))
        return self.updated_currency, self.log_info
