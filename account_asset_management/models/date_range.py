# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
        return super(DateRange, self).create(vals)

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
        return super(DateRange, self).write(vals)
