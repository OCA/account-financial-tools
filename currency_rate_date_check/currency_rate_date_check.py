# -*- encoding: utf-8 -*-
##############################################################################
#
#    Currency rate date check module for OpenERP
#    Copyright (C) 2012-2013 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools.translate import _

# Here are some explainations about the design of this module.
# In server/openerp/addons/base/res/res_currency.py :
# compute() -> _get_conversion_rate() -> _current_rate() -> _current_rate_computation()
# The date used for the rate is the one in the context
# compute() adds currency_rate_type_from and currency_rate_type_to to the context
# _get_conversion_rate() adds currency_rate_type_id to context ; its value is currency_rate_type_to ; if it doesn't exist it's currency_rate_type_from ; if it doesn't exist either it's False
# It already contains raise "No rate found for currency ... at the date ..."
# _current_rate() reads currency_rate_type_id from context and uses it in the SQL request
# This is the function used for the definition of the field.function 'rate' on res_currency

# Which one of the 3 functions should we inherit ? Good question...
# It's probably better to inherit the lowest level function, i.e. _current_rate_computation()
# Advantage : by inheriting the lowest level function, we can be sure that the check
# always apply, even for scenarios where we read the field "rate" of the obj currency
# => that's the solution I implement in the code below


class res_currency(osv.Model):
    _inherit = 'res.currency'

    def _current_rate_computation(self, cr, uid, ids, name, arg, raise_on_no_rate, context=None):
        # We only do the check if there is an explicit date in the context and
        # there is no specific currency_rate_type_id
        if context and context.get('date') and not context.get('currency_rate_type_id') and not context.get('disable_rate_date_check'):
            for currency_id in ids:
                # We could get the company from the currency, but it's not a
                # 'required' field, so we should probably continue to get it from
                # the user, shouldn't we ?
                user = self.pool['res.users'].browse(cr, uid, uid, context=context)
                # if it's the company currency, don't do anything
                # (there is just one old rate at 1.0)
                if user.company_id.currency_id.id == currency_id:
                    continue
                else:
                    # now we do the real work !
                    date = context.get('date', datetime.today().strftime('%Y-%m-%d'))
                    date_datetime = datetime.strptime(date, '%Y-%m-%d')
                    #print "date =", date
                    rate_obj = self.pool['res.currency.rate']
                    selected_rate = rate_obj.search(cr, uid, [
                        ('currency_id', '=', currency_id),
                        ('name', '<=', date),
                        ('currency_rate_type_id', '=', None)
                        ], order='name desc', limit=1, context=context)
                    if not selected_rate:
                        continue

                    rate_date = rate_obj.read(cr, uid, selected_rate[0], ['name'], context=context)['name']
                    rate_date_datetime = datetime.strptime(rate_date, '%Y-%m-%d')
                    max_delta = user.company_id.currency_rate_max_delta
                    #print "max_delta=", max_delta
                    #print "rate_date=", rate_date
                    if (date_datetime - rate_date_datetime).days > max_delta:
                        currency_name = self.read(cr, uid, currency_id, ['name'], context=context)['name']
                        raise osv.except_osv(_('Error'), _('You are requesting a rate conversion on %s for currency %s but the nearest rate before that date is dated %s and the maximum currency rate time delta for your company is %s days') % (date, currency_name, rate_date, max_delta))
        # Now we call the regular function from the "base" module
        return super(res_currency, self)._current_rate_computation(cr, uid, ids, name, arg, raise_on_no_rate, context=context)

