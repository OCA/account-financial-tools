# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# © 2014 Daniel Dico
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface

from openerp import _
from openerp.exceptions import except_orm

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
    name = 'Bank of Canada - noon rates'

    supported_currency_array = [
        "AED", "ANG", "ARS", "AUD", "BOC", "BRL", "BSD", "CHF", "CLP", "CNY",
        "COP", "CZK", "DKK", "EUR", "FJD", "GBP", "GHS", "GTQ", "HKD", "HNL",
        "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JMD", "JPY", "KRW", "LKR",
        "MAD", "MMK", "MXN", "MYR", "NOK", "NZD", "PAB", "PEN", "PHP", "PKR",
        "PLN", "RON", "RSD", "RUB", "SEK", "SGD", "THB", "TND", "TRY", "TTD",
        "TWD", "USD", "VEF", "VND", "XAF", "XCD", "XPF", "ZAR"]

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""

        # as of Jan 2014 BOC is publishing noon rates for about 60 currencies
        url = ('http://www.bankofcanada.ca/stats/assets/'
               'rates_rss/noon/en_%s.xml')
        # closing rates are available as well (please note there are only 12
        # currencies reported):
        # http://www.bankofcanada.ca/stats/assets/rates_rss/closing/en_%s.xml

        # We do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)

        import feedparser
        import pytz
        from dateutil import parser

        for curr in currency_array:

            _logger.debug("BOC currency rate service : connecting...")
            dom = feedparser.parse(url % curr)

            self.validate_cur(curr)

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

            # check for valid exchange data
            if (dom.entries[0].cb_basecurrency == main_currency) and \
                    (dom.entries[0].cb_targetcurrency == curr):
                rate = dom.entries[0].cb_exchangerate.split('\n', 1)[0]
                rate_date_datetime = parser.parse(dom.entries[0].updated)\
                    .astimezone(pytz.utc).replace(tzinfo=None)
                self.check_rate_date(rate_date_datetime, max_delta_days)
                self.updated_currency[curr] = rate
                _logger.debug("BOC Rate retrieved : %s = %s %s" %
                              (main_currency, rate, curr))
            else:
                _logger.error(
                    "Exchange data format error for Bank of Canada -"
                    "%s. Please check provider data format "
                    "and/or source code." % curr)
                raise except_orm(_('Error !'),
                                 _('Exchange data format error for '
                                   'Bank of Canada - %s !' % str(curr)))

        return self.updated_currency, self.log_info
