# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# © 2013-2014 Agustin Cruz openpyme.mx
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface

import logging
_logger = logging.getLogger(__name__)


class MX_BdMGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Banco de México service

    """
    code = 'MX_BdM'
    name = 'Bank of Mexico'
    supported_currency_array = [
        "ARS", "AUD", "BBD", "BMD", "BOB", "BRL", "BSD", "BZD", "CAD", "CHF",
        "CLP", "CNH", "CNY", "COP", "CRC", "CUP", "CZK", "DKK", "DOP", "DZD",
        "EGP", "ESD", "EUR", "FJD", "GBP", "GTQ", "GYD", "HKD", "HNL", "HUF",
        "IDR", "ILS", "INR", "IQD", "JMD", "JPY", "KES", "KRW", "KWD", "MAD",
        "MYR", "NGN", "NIC", "NOK", "NZD", "PAB", "PEN", "PHP", "PLN", "PYG",
        "RON", "RUB", "SAR", "SEK", "SGD", "SVC", "THB", "TRY", "TTD", "TWD",
        "UAH", "USD", "USD", "UYP", "VEF", "VND", "ZAR"]

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
