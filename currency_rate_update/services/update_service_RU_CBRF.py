# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 IT Libertas. All rights reserved.
#    @author Denis Baranov
#
#    Abstract class to fetch rates from Russian Central Bank
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
from xmltodict import parse
import requests

class RU_CBRF_getter(Currency_getter_interface) :
    """Implementation of Currency_getter_factory interface
    for The Central Bank of the Russian Federation service"""
        
    def get_updated_currency(self, currency_array, main_currency, max_delta_days):
        """implementation of abstract method of Currency_getter_interface"""

        response = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
        response.encoding = 'cp1251'
        rates = {}
        text = response.text.encode('utf-8').replace('windows-1251', 'utf-8')
        cbr = parse(text)
        for valute in cbr['ValCurs']['Valute']:
            valute['Value'] = float(valute['Value'].replace(',', '.'))
            rates[valute['CharCode']] = valute['Value']

        if main_currency in currency_array :
            currency_array.remove(main_currency)
        main_currency_data = 1
        if main_currency != 'RUB':
            main_currency_data = rates[main_currency]
            rates['RUB'] = 1

        for curr in currency_array:
            self.validate_cur(curr)
            self.updated_currency[curr] = main_currency_data / rates[curr]
        
        return self.updated_currency, self.log_info
