# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    need_lawsuit = fields.Boolean(string='Needs a lawsuit procedure',
                                  compute='_get_need_lawsuit',
                                  store=True)
    lawsuit_step_id = fields.Many2one(
        comodel_name='account.invoice.lawsuit.step',
        string='Lawsuit Step',
    )

    @api.one
    @api.depends('credit_policy_id',
                 'credit_control_line_ids',
                 'credit_control_line_ids.manually_overridden',
                 'credit_control_line_ids.policy_level_id.policy_id',
                 'credit_control_line_ids.policy_level_id.need_lawsuit',
                 )
    def _get_need_lawsuit(self):
        lines = self.credit_control_line_ids
        if self.credit_policy_id:
            policy = self.credit_policy_id
            lines = lines.filtered(
                lambda line: line.policy_level_id.policy_id == policy
            )
        self.need_lawsuit = any(line.policy_level_id.need_lawsuit
                                for line in lines)
