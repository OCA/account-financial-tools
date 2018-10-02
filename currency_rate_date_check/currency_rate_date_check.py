# -*- coding: utf-8 -*-
# Copyright 2012-2013 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError

# Here are some explainations about the design of this module.
# In odoo/openerp/addons/base/res/res_currency.py :
# compute() -> _get_conversion_rate()
# -> _current_rate() -> _get_current_rate()
# The date used for the rate is the one in the context

# Which one of the 3 functions should we inherit ? Good question...
# It's probably better to inherit the lowest level function,
# i.e. _get_current_rate()
# Advantage : by inheriting the lowest level function,
# we can be sure that the check
# always apply, even for scenarios where we
# read the field "rate" of the obj currency
# => that's the solution I implement in the code below


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.multi
    def _get_current_rate(self, raise_on_no_rate=True):
        # We don't check if we don't have 'date' in context, which is
        # a pb because it means Odoo can do a rate conversion
        # on today's date with an old rate, but otherwize it would raise
        # too often, for example it would raise entering the
        # Currencies menu entry !
        if self.env.context.get('date') and not self.env.context.get(
                'disable_rate_date_check'):
            date = self.env.context.get('date')
            for currency_id in self:
                # We could get the company from the currency, but it's not a
                # 'required' field, so we should probably continue to get it
                # from the user, shouldn't we ?
                user = self.env.user_id
                # if it's the company currency, don't do anything
                # (there is just one old rate at 1.0)
                if user.company_id.currency_id.id == currency_id:
                    continue
                else:
                    # now we do the real work !
                    self.env.cr.execute(
                        'SELECT rate, name FROM res_currency_rate '
                        'WHERE currency_id = %s '
                        'AND name <= %s '
                        'ORDER BY name desc LIMIT 1',
                        (currency_id, date))
                    if self.env.cr.rowcount:
                        rate_date = self.env.cr.fetchone()[1]
                        rate_date_dt = fields.Datetime.from_string(rate_date)
                        date_dt = fields.Datetime.from_string(date)
                        max_delta = user.company_id.currency_rate_max_delta
                        if (date_dt - rate_date_dt).days > max_delta:
                            raise ValidationError(
                                _('You are requesting a rate conversion on %s '
                                  'for currency %s but the nearest '
                                  'rate before that date is '
                                  'dated %s and the maximum currency '
                                  'rate time delta for '
                                  'your company is %s days')
                                % (
                                    date,
                                    currency_id.name,
                                    rate_date,
                                    max_delta)
                                )
        # Now we call the regular function from the "base" module
        return super(ResCurrency, self)._get_current_rate(
            raise_on_no_rate=raise_on_no_rate)
