# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 Educomm. All rights reserved.
#    @author Greg Bognar, Viktor Nagy
#
#    Abstract class to fetch rates from Yahoo Financial
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
from lxml import etree
from datetime import datetime
from suds.client import Client

import logging
_logger = logging.getLogger(__name__)


class HU_MNB_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for the Hungarian National Bank (http://www.mnb.hu)
    """
    WSDL = "http://www.mnb.hu/arfolyamok.asmx?wsdl"

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_cur(main_currency)
        _logger.info("HU_MNB: Updating currencies from Hunagrian National Bank.")
        client = Client(self.WSDL)
        results = etree.fromstring(client.service.GetCurrentExchangeRates())

        date_template = lambda element: element.xpath('//Day')[0].get('date')
        currency_template = lambda element, currency: element.xpath('//Rate[@curr="{0}"]'.format(currency))[0].text

        if main_currency in currency_array:
            _logger.info("HU_MNB: Removing main currency from currency array." + main_currency)
            currency_array.remove(main_currency)

        loaded_currency_date = datetime.strptime(date_template(results), '%Y-%m-%d')

        #this will throw an error if the difference between the 
        #loaded currency date and today is bigger then max_delta_days
        self.check_rate_date(loaded_currency_date, max_delta_days)

        for currency in currency_array:
            self.validate_cur(currency)
            try:
                value = currency_template(results, currency)
            except:
                _logger.error('HU_MNB - Currency Updater - Could not fetch value for {0}'.format(currency))
                continue

            if value:
                _logger.info("Currency: {0} = {1}".format(currency, value))
                self.updated_currency[currency] = float(value.replace(',', '.'))
            else:
                raise Exception('HU_MNB - Currency Updater - Could not update the %s' % (currency))

        _logger.info("HU_MNB: Currency values loaded:")
        return self.updated_currency, self.log_info
