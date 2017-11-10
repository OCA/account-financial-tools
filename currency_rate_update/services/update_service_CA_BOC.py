# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# © 2014 Daniel Dico
# © 2017 Yuriy Gural
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface

from odoo import _
from odoo.exceptions import except_orm

import feedparser
import pytz
from dateutil import parser


import logging
_logger = logging.getLogger(__name__)


class CA_BOCGetter(CurrencyGetterInterface):
    """Implementation of Curreny_getter_factory interface
    for Bank of Canada RSS service

    """
    # Bank of Canada is using RSS-CB
    # http://www.cbwiki.net/wiki/index.php/Specification_1.1
    # This RSS format is used by other national banks
    #  (Thailand, Malaysia, Mexico...)

    code = 'CA_BOC'
    name = 'Bank of Canada'

    supported_currency_array = [
        "AUD", "BRL", "CNY", "EUR", "HKD", "INR", "IDR", "JPY", "RUB", "SAR",
        "SGD", "MYR", "MXN", "NZD", "NOK", "PEN", "ZAR", "KRW", "SEK", "CHF",
        "TWD", "THB", "TRY", "GBP", "USD", "VND", "CAD"]

    def rate_retrieve(self, curr):
        res = {}

        url = ('https://www.bankofcanada.ca/'
               'valet/fx_rss/FX%sCAD') % (curr.upper())

        dom = feedparser.parse(url)

        # check if BOC service is running
        if dom.bozo and dom.status != 404:
            _logger.error("Bank of Canada - service is down - try again\
                later...")

        # check if BOC sent a valid response for this currency
        if dom.status != 200:
            _logger.error("Exchange data for %s is not reported by Bank\
                of Canada." % curr)
            raise except_orm(_('Error !'), _('Exchange data for %s is not '
                                             'reported by Bank of Canada.'
                                             % str(curr)))

        _logger.debug("BOC sent a valid RSS file for: " + curr)

        if (dom.entries[0].cb_basecurrency == 'CAD') and \
                (dom.entries[0].cb_targetcurrency == curr):
            res['rate_currency'] = float(
                dom.entries[0].cb_exchangerate.split('\n', 1)[0]
            )
            res['rate_date_datetime'] = parser.parse(dom.entries[0].updated)\
                .astimezone(pytz.utc).replace(tzinfo=None)
        else:
            _logger.error(
                "Exchange data format error for Bank of Canada -"
                "%s. Please check provider data format "
                "and/or source code." % curr)
            raise except_orm(_('Error !'),
                             _('Exchange data format error for '
                               'Bank of Canada - %s !' % str(curr)))
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""

        url = ('https://www.bankofcanada.ca/'
               'valet/fx_rss/FX%sCAD')
        # closing rates are available as well (please note there are only 12
        # currencies reported):
        # http://www.bankofcanada.ca/stats/assets/rates_rss/closing/en_%s.xml
        # new url:
        # https://www.bankofcanada.ca/valet/fx_rss/FX%sCAD

        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        _logger.debug("BOC currency rate service : connecting...")

        self.validate_cur(main_currency)
        if main_currency != 'CAD':
            main_curr_data = self.rate_retrieve(main_currency)
            self.check_rate_date(main_curr_data['rate_date_datetime'], max_delta_days)

        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'CAD':
                rate = 1 / main_curr_data['rate_currency']
            else:
                curr_data = self.rate_retrieve(curr)
                self.check_rate_date(curr_data['rate_date_datetime'], max_delta_days)
                if main_currency == 'CAD':
                    rate = curr_data['rate_currency']
                else:
                    rate = (curr_data['rate_currency'] /
                            main_curr_data['rate_currency'])
            self.updated_currency[curr] = rate

        return self.updated_currency, self.log_info
