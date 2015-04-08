# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009-TODAY CLEARCORP S.A. (<http://clearcorp.co.cr>).
#    @author Glen Sojo
#
#    Abstract class to fetch rates from Central Bank of Costa Rica
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

from datetime import datetime
from xml.dom.minidom import parseString
from .currency_getter_interface import Currency_getter_interface
from .currency_getter_interface import UnsuportedCurrencyError

# TODO: Extend valid indicators
VALID_INDICATORS = {
    'CRC': [317, 318],
    'EUR': [333],
}
WEBSERVICE_NAME = 'Odoo currency_rate_update'
SUBLEVELS = 'N'


class UnsuportedIndicatorError(Exception):
    def __init__(self, value):
        self.indicator = value

    def __str__(self):
        return 'Unsupported indicator %s' % self.indicator

    def __repr__(self):
        return 'Unsupported indicator %s' % self.indicator


class CR_BCCR_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for BCCR currency update service
    """

    supported_currency_array = [
        'USD',
    ]

    def validate_cur(self, currency):
        """Validate if the currency to update is supported"""
        if currency not in self.supported_currency_array:
            raise UnsuportedCurrencyError(currency)

    def validate_indicator(self, currency_array):
        for currency, indicator in currency_array:
            if indicator not in VALID_INDICATORS[currency]:
                raise UnsuportedIndicatorError(indicator)

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_cur(main_currency)
        self.validate_indicator(currency_array)
        today = datetime.utcnow()

        # Webservice parameters
        date = today.strftime('%d/%m/%Y')

        url = ('http://indicadoreseconomicos.bccr.fi.cr//indicadoreseconomicos'
               '/WebServices/wsIndicadoresEconomicos.asmx/ObtenerIndicadores'
               'Economicos?tcIndicador=%s&tcFechaInicio=%s&tcFechaFinal=%s'
               '&tcNombre=%s&tnSubNiveles=%s')

        # Remove the main currency if it is in the currency_array
        count = 0
        for currency, indicator in currency_array:
            if main_currency == currency:
                currency_array.pop(count)
            count += 1
        for curr, indicator in currency_array:
            res = self.get_url(url % (indicator, date, date,
                                      WEBSERVICE_NAME, SUBLEVELS))
            dom = parseString(res)
            tag = dom.getElementsByTagName('NUM_VALOR')
            val = tag and tag[0].firstChild.data or False
            if val:
                self.updated_currency[curr] = val
            else:
                raise Exception('Could not update the %s' % (curr))
        return self.updated_currency, self.log_info
