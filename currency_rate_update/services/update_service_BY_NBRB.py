# -*- coding: utf-8 -*-
# © 2017 Binh Lam
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime
import logging
import json

from odoo import _
from odoo.exceptions import ValidationError

from .currency_getter_interface import CurrencyGetterInterface

_logger = logging.getLogger(__name__)


class ByNbrpGetter(CurrencyGetterInterface):

    code = 'BY_NBRB'
    name = 'National Bank Of Belarus'
    supported_currency_array = [
        "AUD", "BGN", "UAH", "DKK", "USD", "EUR", "PLN", "IRR", "ISK", "JPY",
        "CAD", "CNY", "KWD", "MDL", "NZD", "NOK", "RUB", "XDR", "SGD", "KGS",
        "KZT", "TRY", "GBP", "CZK", "SEK", "CHF",
    ]

    def rate_retrieve(self, json_data, curr):
        res = {}
        for item in json_data:
            if item['Cur_Abbreviation'] == curr.upper():
                res['rate_currency'] = float(item['Cur_OfficialRate'])
                break
        return res

    def get_updated_currency(
        self,
        currency_array,
        main_currency,
        max_delta_days,
    ):
        """Implementation of abstract method of Curreny_getter_interface."""
        url = 'http://www.nbrb.by/API/ExRates/Rates?Periodicity=0'

        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        _logger.debug("nbrb currency rate service : connecting...")
        rawfile = (self.get_url(url)).decode("utf-8")

        try:
            assert rawfile
            json_data = json.loads(rawfile)
            assert type(json_data) is list and len(json_data) > 0
        except:
            raise ValidationError(_('Exchange data format error for '
                                    'National Bank Of Belarus!'))

        rate_date_datetime = datetime.strptime(
            json_data[0]['Date'],
            '%Y-%m-%dT%H:%M:%S',
        )
        self.check_rate_date(rate_date_datetime, max_delta_days)

        # We dynamically update supported currencies
        self.supported_currency_array = [
            item['Cur_Abbreviation'] for item in json_data
        ]
        self.supported_currency_array.append('BYN')
        _logger.debug("Supported currencies = %s "
                      % self.supported_currency_array)
        self.validate_cur(main_currency)
        if main_currency != 'BYN':
            main_curr_data = self.rate_retrieve(json_data, main_currency)
        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'BYN':
                rate = 1 / main_curr_data['rate_currency']
            else:
                curr_data = self.rate_retrieve(json_data, curr)
                if main_currency == 'BYN':
                    rate = curr_data['rate_currency']
                else:
                    rate = (curr_data['rate_currency'] /
                            main_curr_data['rate_currency'])
            self.updated_currency[curr] = rate
            _logger.debug(
                "Rate retrieved : 1 %s = %s %s" % (main_currency, rate, curr)
            )

        return self.updated_currency, self.log_info
