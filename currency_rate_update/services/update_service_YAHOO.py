# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
#
#    Abstract class to fetch rates from Yahoo Financial
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


class YAHOO_getter(Currency_getter_interface):
    """Implementation of Currency_getter_factory interface
    for Yahoo finance service
    """

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        """implementation of abstract method of curreny_getter_interface"""
        self.validate_cur(main_currency)
        url = ('http://download.finance.yahoo.com/d/'
               'quotes.txt?s="%s"=X&f=sl1c1abg')
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        for curr in currency_array:
            self.validate_cur(curr)
            res = self.get_url(url % (main_currency + curr))
            val = res.split(',')[1]
            if val:
                self.updated_currency[curr] = val
            else:
                raise Exception('Could not update the %s' % (curr))

        return self.updated_currency, self.log_info
