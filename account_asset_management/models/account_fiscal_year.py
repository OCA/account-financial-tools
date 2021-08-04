# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    @api.model
    def create(self, vals):
        date_from = fields.Date.to_date(vals.get('date_from'))
        date_to = fields.Date.to_date(vals.get('date_to'))
        if not date_to == date_from + relativedelta(years=1, days=-1):
            recompute_vals = {
                'reason': 'creation of fiscalyear %s' % vals.get('name'),
                'company_id':
                    vals.get('company_id') or
                    self.env.user.company_id.id,
                'date_trigger': fields.Datetime.now(),
                'state': 'open',
            }
            self.env['account.asset.recompute.trigger'].sudo().create(
                recompute_vals)
        return super().create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('date_from') or vals.get('date_to'):
            for fy in self:
                recompute_vals = {
                    'reason':
                        'duration change of fiscalyear %s' % fy.name,
                    'company_id': fy.company_id.id,
                    'date_trigger': fields.Datetime.now(),
                    'state': 'open',
                }
                self.env['account.asset.recompute.trigger'].sudo().\
                    create(recompute_vals)
        return super().write(vals)
