# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2012-2014 Camptocamp SA
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
from openerp import models, fields, api, _


class CreditControlMarker(models.TransientModel):
    """ Change the state of lines in mass """

    _name = 'credit.control.marker'
    _description = 'Mass marker'

    @api.model
    def _get_line_ids(self):
        context = self.env.context
        if not (context.get('active_model') == 'credit.control.line' and
                context.get('active_ids')):
            return False
        line_obj = self.env['credit.control.line']
        lines = line_obj.browse(context['active_ids'])
        return self._filter_lines(lines)

    name = fields.Selection([('ignored', 'Ignored'),
                             ('to_be_sent', 'Ready To Send'),
                             ('sent', 'Done')],
                            string='Mark as',
                            default='to_be_sent',
                            required=True)
    line_ids = fields.Many2many('credit.control.line',
                                string='Credit Control Lines',
                                default=_get_line_ids,
                                domain="[('state', '!=', 'sent')]")

    @api.model
    @api.returns('credit.control.line')
    def _filter_lines(self, lines):
        """ get line to be marked filter done lines """
        line_obj = self.env['credit.control.line']
        domain = [('state', '!=', 'sent'), ('id', 'in', lines.ids)]
        return line_obj.search(domain)

    @api.model
    @api.returns('credit.control.line')
    def _mark_lines(self, filtered_lines, state):
        """ write hook """
        assert state
        filtered_lines.write({'state': state})
        return filtered_lines

    @api.multi
    def mark_lines(self):
        """ Write state of selected credit lines to the one in entry
        done credit line will be ignored """
        self.ensure_one()

        if not self.line_ids:
            raise api.Warning(_('No credit control lines selected.'))

        filtered_lines = self._filter_lines(self.line_ids)
        if not filtered_lines:
            raise api.Warning(_('No lines will be changed. '
                                'All the selected lines are already done.'))

        self._mark_lines(filtered_lines, self.name)

        return {'domain': unicode([('id', 'in', filtered_lines.ids)]),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'credit.control.line',
                'type': 'ir.actions.act_window'}
