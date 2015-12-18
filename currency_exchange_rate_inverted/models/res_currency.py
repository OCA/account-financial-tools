# -*- coding: utf-8 -*-
# © 2015 Eficent
# © 2015 Techrifiv Solutions Pte Ltd
# © 2015 Statecraft Systems Pte Ltd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    rate_inverted = fields.Boolean('Inverted exchange rate')

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency):
        res = super(ResCurrency, self)._get_conversion_rate(from_currency,
                                                            to_currency)

        if (
            from_currency.rate_inverted and to_currency.rate_inverted or
                not from_currency.rate_inverted and
                not to_currency.rate_inverted):
            return res
        else:
            return 1/res
