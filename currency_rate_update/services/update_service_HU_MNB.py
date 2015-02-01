# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
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
from lxml import html
from datetime import datetime
import requests

import logging
_logger = logging.getLogger(__name__)


class HU_MNB_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for the Hungarian National Bank (http://www.mnb.hu)
    """

    months_to_numbers_mapping = {
        u'január' : 1,
        u'február' : 2,
        u'március' : 3,
        u'április' : 4,
        u'május' : 5,
        u'június' : 6,
        u'július' : 7,
        u'augusztus' : 8,
        u'szeptember' : 9,
        u'október' : 10,
        u'november' : 11,
        u'december' : 12
    }

    def get_date_for_currency(self, site_tree):
        #define a date which surely will throw an error 
        #in the later business logic
        currency_date = datetime(year=1900, month=1, day=1)

        if(site_tree is not None):
            date_path = '//div[@class="MNBDailyRatesUI_ExchangeRates"]/table/thead/tr[1]/td/span'
            date_hun_format = unicode(site_tree.xpath(date_path)[0].text)
            if(date_hun_format is not None):
                date_hun_format = date_hun_format.replace(' ','|')
                date_hun_format = date_hun_format.replace('.','')
                splitted_date = date_hun_format.split('|')
            if(splitted_date is not None and len(splitted_date) == 3):
                currency_date = datetime(year=int(splitted_date[0]), 
                    month=self.months_to_numbers_mapping[splitted_date[1]], 
                    day=int(splitted_date[2]) )
                _logger.info("Date for the MNB curreny is:" + str(currency_date))
            else:
                _logger.warning('Date could not be paresed properly from MNB Webpage, please check xpath mapping or website response.')            
        else:
            _logger.warning('No site_tree was passed to the method, will not return a valid date!')

        return currency_date


    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_cur(main_currency)
        _logger.info("HU_MNB: Updating currencies from Hunagrian National Bank.")
        site_content = requests.get("http://www.mnb.hu/arfolyamok")
        site_tree = html.fromstring(site_content.content)
        path_template = '//div[@class="MNBDailyRatesUI_ExchangeRates"]/table/tbody/tr[{0}]/td[{1}]'

        if main_currency in currency_array:
            _logger.info("HU_MNB: Removing main currency from currency array." + main_currency)
            currency_array.remove(main_currency)

        loaded_currency_date = self.get_date_for_currency(site_tree)

        #this will throw an error if the difference between the 
        #loaded currency date and today is bigger then max_delta_days
        self.check_rate_date(loaded_currency_date, max_delta_days)

        currencies_and_values = {}

        # there are 17 columns on the HTML page
        for i in range(1, 18):
            currency1 = site_tree.xpath(path_template.format(i,1))[0].text
            val1 = site_tree.xpath(path_template.format(i,4))[0].text
            currency2 = site_tree.xpath(path_template.format(i,6))[0].text
            val2 = site_tree.xpath(path_template.format(i,9))[0].text
        
            currencies_and_values[currency1] = float(val1.replace(',','.'))
            currencies_and_values[currency2] = float(val2.replace(',','.'))

        _logger.info("HU_MNB: Currency values loaded:")
        _logger.info(currencies_and_values)

        for curr in currency_array:
            self.validate_cur(curr)
            
            val = currencies_and_values[curr];
            if val:
                _logger.info("Currency: {0} = {1}".format(curr, val))
                self.updated_currency[curr] = val
            else:
                raise Exception('HU_MNB - Currency Updater - Could not update the %s' % (curr))

        return self.updated_currency, self.log_info
