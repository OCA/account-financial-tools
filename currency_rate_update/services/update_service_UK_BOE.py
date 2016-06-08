# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi

#    Abstract class to fetch rates from Bank of England
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

from openerp import _
from openerp.exceptions import except_orm

from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from lxml import etree

import logging
_logger = logging.getLogger(__name__)


currency_key = {
    "AUD": ["EC3", "XUDLADS"],
    "CAD": ["ECL", "XUDLCDS"],
    "CNY": ["INB", "XUDLBK89"],
    "CZK": ["DS7", "XUDLBK25"],
    "DKK": ["ECH", "XUDLDKS"],
    "EUR": ["C8J", "XUDLERS"],
    "HKD": ["ECN", "XUDLHDS"],
    "HUF": ["5LA", "XUDLBK33"],
    "INR": ["INE", "XUDLBK97"],
    "ILS": ["IN7", "XUDLBK78"],
    "JPY": ["C8N", "XUDLJYS"],
    "MYR": ["IN8", "XUDLBK83"],
    "NZD": ["ECO", "XUDLNDS"],
    "NOK": ["EC6", "XUDLNKS"],
    "PLN": ["5OW", "XUDLBK47"],
    "RUB": ["IN9", "XUDLBK85"],
    "SAR": ["ECZ", "XUDLSRS"],
    "SGD": ["ECQ", "XUDLSGS"],
    "ZAR": ["ECE", "XUDLZRS"],
    "KRW": ["INC", "XUDLBK93"],
    "SEK": ["ECC", "XUDLSKS"],
    "CHF": ["ECU", "XUDLSFS"],
    "TWD": ["ECD", "XUDLTWS"],
    "THB": ["INA", "XUDLBK87"],
    "TRY": ["IND", "XUDLBK95"],
    "USD": ["C8P", "XUDLUSS"],
}


class UK_BOE_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for BOE service

    """

    def rate_retrieve(self, currency_string):

        res = {}
        now = datetime.now()
        url = ("http://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp?"
               "CodeVer=new&xml.x=yes&FromSeries=1&ToSeries=50&DAT=RNG&VFD=Y&CSVF=TT&Filter=N&"
               "C=%s&FD=%s&FM=%s&FY=%s&TD=%s&TM=%s&TY=%s" 
               % (currency_string, 
                  now.day,  now.strftime("%b"), now.year-1, 
                  now.day, now.strftime("%b"), now.year))

        _logger.debug("BOE currency rate service : connecting...")

        tree = etree.parse(url)
        envelope = tree.getroot()
        currencies = envelope.getchildren()

        for currency in currencies:
            currency_code = currency.xpath('@SCODE')[0]
            for key, value in currency_key.items():
                if value[1] == currency_code:
                    currency_abbreviation = key
            updates = currency.getchildren()
            for update in updates:
                if update.xpath('@LAST_OBS'):
                    update_date = update.xpath('@LAST_OBS')[0]
                if update.xpath('@TIME'):
                    update_time = update.xpath('@TIME')[0]
                    if update_date == update_time:
                        update_rate = update.xpath('@OBS_VALUE')[0]
            res[currency_abbreviation] = {
                'date': update_date,
                'rate': update_rate,
            }

        _logger.debug("BOE sent a valid XML file")

        return res


    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Currency_getter_interface"""

        """
From BoE website: "The data represent indicative middle market 
(mean of spot buying and selling) rates as observed by the 
Bank's Foreign Exchange Desk in the London interbank market around 4pm.
        """

        currency_string = ",".join([currency_key[curr][0] for curr in currency_array])

        if main_currency not in currency_array and main_currency != "GBP":
            currency_array = ",".join([currency_array, main_currency])

        rate_update = self.rate_retrieve(currency_string)

        if main_currency != "GBP":
            main_curr_rate = rate_update[main_currency]['rate']
        else:
            main_curr_rate = 1.0

        for curr, update in rate_update.items():
            # We do not want to update the main currency
            if curr != main_currency:
                rate_date_datetime = datetime.strptime(update['date'],
                                                   DEFAULT_SERVER_DATE_FORMAT)
                self.check_rate_date(rate_date_datetime, max_delta_days)
                self.updated_currency[curr] = float(update['rate']) / main_curr_rate
                _logger.debug("BOE Rate retrieved : %s = %s %s" %
                              (main_currency, update['rate'], curr))

        return self.updated_currency, self.log_info
