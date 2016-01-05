# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    @api.multi
    def name_get(self):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param ids: list of ids for which name should be read
        @param context: context arguments, like lang, time zone

        @return: Returns a list of tupples containing id, name
        """
        if not self:
            return []
        res = []
        for rate in self:
            rate_datetime = fields.Datetime.from_string(rate.name)
            rate_date = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(rate, rate_datetime))
            name = "%s - %s (%s)" % (rate_date, rate.currency_id.name,
                                     rate.rate)
            res += [(rate.id, name)]
        return res
