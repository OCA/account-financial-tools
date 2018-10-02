# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    use_journal_setting = fields.Boolean(
        'Use journal setting to post journal entries '
        'on invoice and bank statement validation',
    )

    @api.multi
    def set_parameters(self):
        self.ensure_one()
        config_pool = self.env['ir.config_parameter']
        if self.use_journal_setting:
            config_pool.set_param(
                'use_journal_setting',
                self.use_journal_setting)
        else:
            # remove the key from parameter
            ids = config_pool.search([('key', '=', 'use_journal_setting')])
            ids.unlink()

    @api.model
    def default_get(self, fields):
        res = super(AccountConfigSettings, self).default_get(fields)
        config_pool = self.env['ir.config_parameter']
        res['use_journal_setting'] = config_pool.get_param(
            'use_journal_setting')
        return res
