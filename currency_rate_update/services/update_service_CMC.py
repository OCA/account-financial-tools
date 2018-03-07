# -*- coding: utf-8 -*-
# © 2018 Ross Golder
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface

import logging
_logger = logging.getLogger(__name__)

import json


class CMCGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for coinmarketcap.com cryptocurrency information service
    """
    code = 'CMC'
    name = 'Coin Market Cap'

    supported_currency_array = [
        "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR", "GBP",
        "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", "MXN", "MYR", "NOK",
        "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB", "TRY", "TWD",
        "ZAR", "USD",
        "BTC", "ETH", "LTC"
    ]

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_cur(main_currency)
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        url = 'https://api.coinmarketcap.com/v1/ticker/%s/?convert=' + main_currency
        ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'LTC': 'litecoin',
        }
        for curr in currency_array:
            curr_id = ids[curr]
            res = self.get_url(url % curr_id)
            val = json.loads(res)
            attr = ("price_" + main_currency).lower()
            if val:
                self.updated_currency[curr] = val[0][attr]
            else:
                raise Exception('Could not update the %s' % (curr))

        return self.updated_currency, self.log_info
