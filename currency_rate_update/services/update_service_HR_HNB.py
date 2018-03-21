# -*- coding: utf-8 -*-
# Copyright © 2018 DAJ MI 5 <http://www.dajmi5.hr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from .currency_getter_interface import CurrencyGetterInterface
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)


class HrHnbGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface for HR HNB service"""

    code = 'HR_HNB'
    name = 'Hrvatska narodna banka'
    supported_currency_array = [
        "AUD", "CAD", "CHF", "CZK", "DKK", "EUR", "GBP", "HUF", "JPY", "NOK",
        "PLN", "SEK", "USD"]

    def get_updated_currency(self, currency_array, main_currency, max_delta_days):

        # we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        rate_date = self.rate_date or datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_str = datetime.strftime(datetime.strptime(rate_date, DEFAULT_SERVER_DATE_FORMAT), '%d%m%y')
        rawfile = self.get_url('http://www.hnb.hr/tecajn/f%s.dat' % date_str)

        curr_rates = {}
        line_number = 0
        for line in rawfile.splitlines():
            line_number += 1
            if line_number == 1:
                continue
            line = line.split()
            if len(line) == 4:
                curr = line[0][3:6]
                num_of_units = float(line[0][6:9])
                curr_rates[curr] = {
                    'rate_buy': round(num_of_units / float(line[1].replace(',', '.')), 6),
                    'rate_avg': round(num_of_units / float(line[2].replace(',', '.')), 6),
                    'rate_sell': round(num_of_units / float(line[3].replace(',', '.')), 6),
                }

        for curr in currency_array:
            self.validate_cur(curr)
            if curr in curr_rates.keys():
                self.updated_currency[curr] = curr_rates[curr][self.rate_type]
                _logger.debug('Rate retrieved: %s = %s %s' % (main_currency, curr_rates[curr][self.rate_type], curr))

        return self.updated_currency, self.log_info
