# -*- coding: utf-8 -*-
# © 2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface

import re


class GOOGLEGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Google currency conversion service
    """
    code = 'GOOGLE'
    name = 'Google Currency Converter'

    supported_currency_array = [
        "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
        "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BRL",
        "BSD", "BTN", "BWP", "BYR", "BZD", "CAD", "CDF", "CHF", "CLF", "CLP",
        "CNH", "CNY", "COP", "CRC", "CUP", "CVE", "CZK", "DJF", "DKK", "DOP",
        "DZD", "EGP", "ERN", "ETB", "EUR", "FJD", "FKP", "GBP", "GEL", "GHS",
        "GIP", "GMD", "GNF", "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG", "HUF",
        "IDR", "IEP", "ILS", "INR", "IQD", "IRR", "ISK", "JMD", "JOD", "JPY",
        "KES", "KGS", "KHR", "KMF", "KPW", "KRW", "KWD", "KYD", "KZT", "LAK",
        "LBP", "LKR", "LRD", "LSL", "LTL", "LVL", "LYD", "MAD", "MDL", "MGA",
        "MKD", "MMK", "MNT", "MOP", "MRO", "MUR", "MVR", "MWK", "MXN", "MXV",
        "MYR", "MZN", "NAD", "NGN", "NIO", "NOK", "NPR", "NZD", "OMR", "PAB",
        "PEN", "PGK", "PHP", "PKR", "PLN", "PYG", "QAR", "RON", "RSD", "RUB",
        "RWF", "SAR", "SBD", "SCR", "SDG", "SEK", "SGD", "SHP", "SLL", "SOS",
        "SRD", "STD", "SVC", "SYP", "SZL", "THB", "TJS", "TMT", "TND", "TOP",
        "TRY", "TTD", "TWD", "TZS", "UAH", "UGX", "USD", "UYU", "UZS", "VEF",
        "VND", "VUV", "WST", "XAF", "XAG", "XAU", "XCD", "XCP", "XDR", "XOF",
        "XPD", "XPF", "XPT", "YER", "ZAR", "ZMW", "ZWL", "BTC"]

    # We can get a more accurate decimal rate by converting the other way
    invert_currencies = [
        "BTC",
    ]

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of currency_getter_interface"""
        self.validate_cur(main_currency)
        url = ('https://www.google.com/finance/'
               'converter?a=1&from=%s&to=%s')
        regexp = re.compile(r'<span class=bld>(.*)</span>')
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        for curr in currency_array:
            self.validate_cur(curr)
            if curr in self.invert_currencies:
                res = self.get_url(url % (curr, main_currency))
            else:
                res = self.get_url(url % (main_currency, curr))
            match = regexp.search(res)
            if match:
                val = match.group()[16:-11]
                if curr in self.invert_currencies:
                    val = str(1.0 / float(val))
                self.updated_currency[curr] = val
            else:
                raise Exception('Could not update the %s' % (curr))

        return self.updated_currency, self.log_info
