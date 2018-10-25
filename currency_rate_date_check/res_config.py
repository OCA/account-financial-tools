# -*- coding: utf-8 -*-
# Copyright 2018 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import fields, models, api


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    activate_currency_rate_max_delta = fields.Boolean(
        default=False, string='Activate check of the max date rate',
        help="This must be true to execute the validation of Max Time Delta "
        "in Days for Currency Rates")

    @api.model
    def _default_company(self):
        return self.env.user.company_id

    @api.model
    def default_get(self, fields):
        res = super(BaseConfigSettings, self).default_get(fields)
        company_id = self._default_company()
        max_delta_activate = company_id.activate_currency_rate_max_delta
        res.update({
            'activate_currency_rate_max_delta': max_delta_activate
        })
        return res

    @api.multi
    def set_activate_currency_rate_max_delta(self):
        """Activate currency rate max delta validation"""
        for record in self:
            company_id = self._default_company()
            company_id.activate_currency_rate_max_delta = \
                record.activate_currency_rate_max_delta
