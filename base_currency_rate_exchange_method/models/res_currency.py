# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 Andhitia Rama. All rights reserved.
#    @author Andhitia Rama
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

from openerp import models
from openerp.addons.base.res.res_currency import res_currency
import time
from openerp.tools.translate import _
from openerp.osv import osv


def _get_conversion_rate(
        self, cr, uid, from_currency, to_currency, context=None):
    if context is None:
        context = {}
    ctx = context.copy()
    from_currency = self.browse(cr, uid, from_currency.id, context=ctx)
    to_currency = self.browse(cr, uid, to_currency.id, context=ctx)
    obj_user = self.pool.get('res.users')
    user = obj_user.browse(cr, uid, uid)
    exchange_rate_method = user.company_id.exchange_rate_method

    if from_currency.rate == 0 or to_currency.rate == 0:
        date = context.get('date', time.strftime('%Y-%m-%d'))
        if from_currency.rate == 0:
            currency_symbol = from_currency.symbol
        else:
            currency_symbol = to_currency.symbol
        msg = _("""No rate found \n
                for the currency: %s \n
                at the date %s
                """) % (currency_symbol, date)

        raise osv.except_osv(_('Error'), msg)
    if exchange_rate_method == 'direct':
        return from_currency.rate / to_currency.rate
    else:
        return to_currency.rate / from_currency.rate


class ResCurrencyHookGetConversionRate(models.AbstractModel):
    _name = 'res.company.hook.get.conversion.rate'
    _description = 'Provide hook point to res.company\'s _get_conversion_rate'

    def _register_hook(self, cr):
        res_currency._get_conversion_rate = _get_conversion_rate
