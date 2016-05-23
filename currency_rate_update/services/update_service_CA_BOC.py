# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
#
#    Abstract class to fetch rates from Bank of Canada
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

import logging
_logger = logging.getLogger(__name__)


class CA_BOC_getter(Currency_getter_interface):
    """Implementation of Curreny_getter_factory interface
    for Bank of Canada RSS service

    """

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of Curreny_getter_interface"""

        # as of Jan 2014 BOC is publishing noon rates for about 60 currencies
        # currency codes in the XML file have the suffix "_NOON" or "_CLOSE" as
        # of April 2015
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
                    (dom.entries[0].cb_targetcurrency[:3] == curr):
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
