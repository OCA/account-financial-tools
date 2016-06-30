# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# © 2009 Grzegorz Grzelak
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface

from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)


class PL_NBPGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for PL NBP service

    """
    code = 'PL_NBP'
    name = 'National Bank of Poland'

    supported_currency_array = [
        "AUD", "BGN", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR",
        "GBP", "HKD", "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW",
        "LTL", "MXN", "MYR", "NOK", "NZD", "PHP", "PLN", "RON", "RUB", "SEK",
        "SGD", "THB", "TRY", "UAH", "USD", "XDR", "ZAR"]

    def rate_retrieve(self, dom, ns, curr):
        """ Parse a dom node to retrieve
        currencies data"""
        res = {}
        xpath_rate_currency = ("/tabela_kursow/pozycja[kod_waluty='%s']/"
                               "kurs_sredni/text()") % (curr.upper())
        xpath_rate_ref = ("/tabela_kursow/pozycja[kod_waluty='%s']/"
                          "przelicznik/text()") % (curr.upper())
        res['rate_currency'] = float(
            dom.xpath(xpath_rate_currency, namespaces=ns)[0].replace(',', '.')
        )
        res['rate_ref'] = float(dom.xpath(xpath_rate_ref, namespaces=ns)[0])
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""
        # LastA.xml is always the most recent one
        url = 'http://www.nbp.pl/kursy/xml/LastA.xml'
        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        # Move to new XML lib cf Launchpad bug #645263
        from lxml import etree
        _logger.debug("NBP.pl currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        ns = {}  # Cool, there are no namespaces !
        _logger.debug("NBP.pl sent a valid XML file")
        rate_date = dom.xpath('/tabela_kursow/data_publikacji/text()',
                              namespaces=ns)[0]
        rate_date_datetime = datetime.strptime(rate_date,
                                               DEFAULT_SERVER_DATE_FORMAT)
        self.check_rate_date(rate_date_datetime, max_delta_days)
        # We dynamically update supported currencies
        self.supported_currency_array = dom.xpath(
            '/tabela_kursow/pozycja/kod_waluty/text()',
            namespaces=ns
        )
        self.supported_currency_array.append('PLN')
        _logger.debug("Supported currencies = %s" %
                      self.supported_currency_array)
        self.validate_cur(main_currency)
        if main_currency != 'PLN':
            main_curr_data = self.rate_retrieve(dom, ns, main_currency)
            # 1 MAIN_CURRENCY = main_rate PLN
            main_rate = (main_curr_data['rate_currency'] /
                         main_curr_data['rate_ref'])
        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'PLN':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve(dom, ns, curr)
                # 1 MAIN_CURRENCY = rate CURR
                if main_currency == 'PLN':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = (main_rate * curr_data['rate_ref'] /
                            curr_data['rate_currency'])
            self.updated_currency[curr] = rate
            _logger.debug("Rate retrieved : %s = %s %s" %
                          (main_currency, rate, curr))
        return self.updated_currency, self.log_info
