# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 HacBee UAB. All rights reserved.
#    @author Darko Nikolovski
#
#    Abstract class to fetch rates from National Bank of the Republic of Macedonia
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

from .currency_getter_interface import CurrencyGetterInterface

from datetime import datetime
from pysimplesoap.client import SoapClient
from lxml import etree
from openerp import exceptions, _

import logging
_logger = logging.getLogger(__name__)


class MK_NBRMGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface for NBRM service"""
    
    code = 'MK_NBRM'
    name = 'National Bank of the Republic of Macedonia'
    supported_currency_array = [
    "EUR", "USD", "GBP", "CHF", "SEK", "NOK", "JPY", "DKK", "CAD", "AUD",
    "BGN", "CZK", "HUF", "PLN", "RON", "HRK", "TRY", "RUB", "BRL", "CNY",
    "HKD", "IDR", "ILS", "INR", "KRW", "MXN", "MYR", "NZD", "PHP", "SGD",
    "THB", "ZAR"]
    
    def rate_retrieve(self, dom, ns, curr):
        """ Parse a dom node to retrieve-
        currencies data"""
        res = {}
        xpath_rate_currency = ("KursZbir[Oznaka='%s']/Sreden/text()"
                               % (curr.upper()))

        res['rate_currency'] = 1 / float(dom.xpath(xpath_rate_currency,
                                                   namespaces=ns)[0])
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""

        url = 'http://www.nbrm.mk/klservice/kurs.asmx?wsdl'

        # we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)

        client = SoapClient(wsdl=url, trace=False)

        # Get currencies for current day:
        rate_data_str = datetime.now().strftime('%d.%m.%Y')

        # There are no namespaces.
        ns = {}
        _logger.debug("NBRM currency rate service : connecting...")
        result = client.GetExchangeRate(StartDate=rate_data_str,
                                        EndDate=rate_data_str)
        
        try:
            dom = etree.fromstring(result['GetExchangeRateResult'])
        except:
            raise exceptions.Warning(
                    _('Error occurred during getting currencies from NBRM'))
            _logger.debug("The Service NBRM returned error: %s" % result)

        _logger.debug("Received currency list from NBRM!")

        rate_date = dom.xpath("KursZbir/Datum/text()", namespaces=ns)[0]
        rate_date_datetime = datetime.strptime(rate_date.split('T')[0],
                                               "%Y-%m-%d")
        self.check_rate_date(rate_date_datetime, max_delta_days)

        # we dynamically update supported currencies
        self.supported_currency_array = dom.xpath(
                                        "KursZbir/Oznaka/text()",
                                        namespaces=ns)

        self.supported_currency_array.append('MKD')
        _logger.debug("Supported currencies = %s" %
                      self.supported_currency_array)

        self.validate_cur(main_currency)
        if main_currency != 'MKD':
            main_curr_data = self.rate_retrieve(dom, ns, main_currency)

        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'MKD':
                rate = 1 / main_curr_data['rate_currency']
            else:
                curr_data = self.rate_retrieve(dom, ns, curr)
                if main_currency == 'MKD':
                    rate = curr_data['rate_currency']
                else:
                    rate = (curr_data['rate_currency'] /
                            main_curr_data['rate_currency'])

            self.updated_currency[curr] = rate
            _logger.debug(
                "Rate retrieved : 1 %s = %s %s" % (main_currency, rate, curr))

        return self.updated_currency, self.log_info
