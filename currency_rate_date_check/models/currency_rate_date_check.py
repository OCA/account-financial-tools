# coding: utf-8
# © 2014 Today Akretion
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import Warning

# Here are some explainations about the design of this module.
# In odoo/odoo/addons/base/res/res_currency.py :
# compute() -> _get_conversion_rate()
# -> _current_rate() -> _get_current_rate()
# The date used for the rate is the one in the self.env.context

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
    def _compute_current_rate(self):
        # We don't check if we don't have 'date' in self.env.context, which is
        # a pb because it means Odoo can do a rate conversion
        # on today's date with an old rate, but otherwize it would raise
        # too often, for example it would raise entering the
        # Currencies menu entry !
        if self.env.context.get('date') and\
                not self.env.context.get('disable_rate_date_check'):
            date = self.env.context.get('date')
            for currency in self:
                # We could get the company from the currency, but it's not a
                # 'required' field, so we should probably continue to get it
                # from the user, shouldn't we ?
                user = self.env.user
                # if it's the company currency, don't do anything
                # (there is just one old rate at 1.0)
                if user.company_id.currency_id == currency:
                    continue
                else:
                    # now we do the real work !
                    company_id = self.env.context.get('company_id') or\
                        self.env['res.users']._get_company().id
                    query = """
                            SELECT r.rate, r.name FROM res_currency_rate r
                            WHERE r.name <= %s
                            AND (r.company_id IS NULL OR r.company_id = %s)
                            AND r.currency_id = %s
                        ORDER BY r.company_id, r.name DESC LIMIT 1"""
                    self.env.cr.execute(
                        query, (date, company_id, currency.id))
                    if self.env.cr.rowcount:
                        rate_date = self.env.cr.fetchone()[1]
                        rate_date_dt = fields.Datetime.from_string(rate_date)
                        date_dt = fields.Datetime.from_string(date)
                        max_delta = user.company_id.currency_rate_max_delta
                        if (date_dt - rate_date_dt).days > max_delta:
                            raise Warning(
                                _('You are requesting a rate conversion on %s '
                                  'for currency %s but the nearest '
                                  'rate before that date is '
                                  'dated %s and the maximum currency '
                                  'rate time delta for '
                                  'your company is %s days')
                                % (date, currency.name, rate_date, max_delta))
        # Now we call the regular function from the "base" module
        return super(ResCurrency, self)._compute_current_rate()
