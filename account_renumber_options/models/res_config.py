# -*- coding: utf-8 -*-
# Copyright 2017 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    renumber_by_period = fields.Boolean(
        string='Renumber account moves by period',
        help='When this check is not marked the account renumber will be done '
        'not taking into account the period of each move, however if the check'
        ' is marked, the account move renumbering will be done normally.')

    @api.multi
    def set_parameters(self):
        config_pool = self.env['ir.config_parameter']
        if self.renumber_by_period:
            config_pool.set_param('renumber_by_period',
                                  self.renumber_by_period)
        else:
            # remove the key from parameter
            ids = config_pool.search([('key', '=', 'renumber_by_period')],)
            if ids:
                ids.unlink()

    @api.model
    def default_get(self, fields):
        res = super(AccountConfigSettings, self).default_get(fields)
        config_pool = self.env['ir.config_parameter']
        res['renumber_by_period'] = config_pool.get_param(
            'renumber_by_period', False)
        return res
