# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
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


class AbstractClassError(Exception):
    def __str__(self):
        return 'Abstract Class'

    def __repr__(self):
        return 'Abstract Class'


class AbstractMethodError(Exception):
    def __str__(self):
        return 'Abstract Method'

    def __repr__(self):
        return 'Abstract Method'


class UnknowClassError(Exception):
    def __str__(self):
        return 'Unknown Class'

    def __repr__(self):
        return 'Unknown Class'


class UnsuportedCurrencyError(Exception):
    def __init__(self, value):
        self.curr = value

    def __str__(self):
        return 'Unsupported currency %s' % self.curr

    def __repr__(self):
        return 'Unsupported currency %s' % self.curr


class Currency_getter_factory():
    """Factory pattern class that will return
    a currency getter class base on the name passed
    to the register method

    """
    def register(self, class_name):
        allowed = [
            'CH_ADMIN_getter',
            'PL_NBP_getter',
            'ECB_getter',
            'GOOGLE_getter',
            'YAHOO_getter',
            'MX_BdM_getter',
            'CA_BOC_getter',
            'RO_BNR_getter',
        ]
        if class_name in allowed:
            exec "from .update_service_%s import %s" % \
                 (class_name.replace('_getter', ''), class_name)
            class_def = eval(class_name)
            return class_def()
        else:
            raise UnknowClassError
