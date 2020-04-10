# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class DateRange(models.Model):
    _inherit = 'date.range'

    @api.model
    def create(self, vals):
        # TODO:
        # change logic to avoid table recompute overhead
        # when a regular (duration = 1 year) new FY is created
        fy_types = self.env['date.range.type'].search(
            [('fiscal_year', '=', True)])
        if vals.get('type_id') in fy_types._ids:
            recompute_vals = {
                'reason': 'creation of fiscalyear %s' % vals.get('code'),
                'company_id':
                    vals.get('company_id') or
                    self.env.user.company_id.id,
                'date_trigger': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'state': 'open',
            }
            self.env['account.asset.recompute.trigger'].sudo().create(
                recompute_vals)
        return super().create(vals)

    @api.multi
    def write(self, vals):
        fy_types = self.env['date.range.type'].search(
            [('fiscal_year', '=', True)])
        if vals.get('type_id') in fy_types.ids:
            if vals.get('date_start') or vals.get('date_end'):
                for fy in self:
                    recompute_vals = {
                        'reason':
                            'duration change of fiscalyear %s' % fy.name,
                        'company_id': fy.company_id.id,
                        'date_trigger':
                            time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'state': 'open',
                    }
                    self.env['account.asset.recompute.trigger'].sudo().\
                        create(recompute_vals)
        return super().write(vals)
