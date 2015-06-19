# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
#
#    Abstract class to fetch rates from National Bank of Romania
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

from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


class RO_BNR_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface for BNR service"""

    def rate_retrieve(self, dom, ns, curr):
        """ Parse a dom node to retrieve-
        currencies data"""
        res = {}
        xpath_rate_currency = "/def:DataSet/def:Body/def:Cube/def:Rate" + \
                              "[@currency='%s']/text()" % (curr.upper())
        xpath_rate_ref = "/def:DataSet/def:Body/def:Cube/def:Rate" + \
                         "[@currency='%s']/@multiplier" % (curr.upper())
        res['rate_currency'] = float(dom.xpath(xpath_rate_currency,
                                               namespaces=ns)[0])
        try:
            res['rate_ref'] = float(dom.xpath(xpath_rate_ref,
                                              namespaces=ns)[0])
        except:
            res['rate_ref'] = 1
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        url = 'http://www.bnr.ro/nbrfxrates.xml'
        # we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("BNR currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        adminch_ns = {'def': 'http://www.bnr.ro/xsd'}
        rate_date = dom.xpath('/def:DataSet/def:Body/def:Cube/@date',
                              namespaces=adminch_ns)[0]
        rate_date_datetime = datetime.strptime(rate_date, '%Y-%m-%d') + \
            timedelta(days=1)
        self.check_rate_date(rate_date_datetime, max_delta_days)
        # we dynamically update supported currencies
        self.supported_currency_array = dom.xpath(
            "/def:DataSet/def:Body/" + "def:Cube/def:Rate/@currency",
            namespaces=adminch_ns)
        self.supported_currency_array = [
            x.upper() for x in self.supported_currency_array]
        self.supported_currency_array.append('RON')

        self.validate_cur(main_currency)
        if main_currency != 'RON':
            main_curr_data = self.rate_retrieve(dom, adminch_ns, main_currency)
            # 1 MAIN_CURRENCY = main_rate RON
            main_rate = main_curr_data['rate_currency'] / \
                main_curr_data['rate_ref']
        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'RON':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve(dom, adminch_ns, curr)
                # 1 MAIN_CURRENCY = rate CURR
                if main_currency == 'RON':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = main_rate * curr_data['rate_ref'] / \
                        curr_data['rate_currency']
            self.updated_currency[curr] = rate
            _logger.debug("BNR Rate retrieved : 1 " + main_currency + ' = ' +
                          str(rate) + ' ' + curr)
        return self.updated_currency, self.log_info
