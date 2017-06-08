# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, exceptions, _


class CreditControlPolicyLevel(models.Model):
    """Add lawsuits to policy level"""

    _inherit = "credit.control.policy.level"

    need_lawsuit = fields.Boolean(string='Needs a Lawsuit procedure')

    @api.constrains('need_lawsuit')
    def _check_lawsuit_level(self):
        for current_level in self:
            levels = current_level.policy_id.level_ids
            highest = max(levels, key=lambda x: x.level)
            for level in levels:
                if level.need_lawsuit and level != highest:
                    raise exceptions.Warning(
                        _('Only the highest level can be selected for '
                          'lawsuits. The highest level is %s') % highest.name
                    )
