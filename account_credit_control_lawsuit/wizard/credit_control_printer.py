# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2015 Camptocamp SA
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


class CreditControlPrinter(models.TransientModel):
    _inherit = "credit.control.printer"

    @api.model
    def _get_line_ids(self):
        context = self.env.context
        if context.get('active_model') != 'credit.control.line':
            return False
        line_ids = context.get('active_ids', False)
        if not line_ids:
            return
        line_model = self.env['credit.control.line']
        lines = line_model.browse(line_ids)
        return lines.filtered(lambda line: (not
                                            line.policy_level_id.need_lawsuit))

    line_ids = fields.Many2many(
        domain=[('policy_level_id.need_lawsuit', '=', False)],
        default=_get_line_ids
    )
