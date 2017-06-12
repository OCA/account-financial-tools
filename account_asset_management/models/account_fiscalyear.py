# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
from datetime import datetime
import time

from openerp import api, models
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AccountFiscalyear(models.Model):
    _inherit = 'account.fiscalyear'

    @api.model
    def create(self, vals):
        date_start = datetime.strptime(vals['date_start'], '%Y-%m-%d')
        date_stop = datetime.strptime(vals['date_stop'], '%Y-%m-%d')
        fy_duration = (date_stop - date_start).days + 1
        year = int(vals['date_start'][:4])
        cy_days = calendar.isleap(year) and 366 or 365
        if fy_duration != cy_days:
            recompute_vals = {
                'reason': 'creation of fiscalyear %s' % vals.get('code'),
                'company_id':
                    vals.get('company_id') or
                    self.env.user.company_id.id,
                'date_trigger': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'state': 'open'}
            self.env['account.asset.recompute.trigger'].sudo().create(
                recompute_vals)
        return super(AccountFiscalyear, self).create(vals)

    @api.multi
    def write(self, vals):
        dates = ['date_start', 'date_stop']
        if any([vals.get(f) for f in dates]):
            for fy in self:
                for f in dates:
                    if f in vals and vals[f] != getattr(fy, f):
                        recompute_vals = {
                            'reason':
                                'duration change of fiscalyear %s' % fy.code,
                            'company_id': fy.company_id.id,
                            'date_trigger':
                                time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'state': 'open'}
                        self.env['account.asset.recompute.trigger'].sudo().\
                            create(recompute_vals)
                        break
        return super(AccountFiscalyear, self).write(vals)
