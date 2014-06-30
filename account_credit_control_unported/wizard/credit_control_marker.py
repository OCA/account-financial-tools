# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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
from openerp.osv import orm, fields
from openerp.tools.translate import _


class CreditControlMarker(orm.TransientModel):
    """Change the state of lines in mass"""

    _name = 'credit.control.marker'
    _description = 'Mass marker'

    def _get_line_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = False
        if (context.get('active_model') == 'credit.control.line' and
                context.get('active_ids')):
            res = self._filter_line_ids(
                    cr, uid,
                    context['active_ids'],
                    context=context)
        return res

    _columns = {
        'name': fields.selection([('ignored', 'Ignored'),
                                  ('to_be_sent', 'Ready To Send'),
                                  ('sent', 'Done')],
                                  'Mark as', required=True),
        'line_ids': fields.many2many(
            'credit.control.line',
            string='Credit Control Lines',
            domain="[('state', '!=', 'sent')]"),
    }

    _defaults = {
        'name': 'to_be_sent',
        'line_ids': _get_line_ids,
    }

    def _filter_line_ids(self, cr, uid, active_ids, context=None):
        """get line to be marked filter done lines"""
        line_obj = self.pool.get('credit.control.line')
        domain = [('state', '!=', 'sent'), ('id', 'in', active_ids)]
        return line_obj.search(cr, uid, domain, context=context)

    def _mark_lines(self, cr, uid, filtered_ids, state, context=None):
        """write hook"""
        line_obj = self.pool.get('credit.control.line')
        if not state:
            raise ValueError(_('state can not be empty'))
        line_obj.write(cr, uid, filtered_ids, {'state': state}, context=context)
        return filtered_ids

    def mark_lines(self, cr, uid, wiz_id, context=None):
        """Write state of selected credit lines to the one in entry
        done credit line will be ignored"""
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
                "wiz_id: only one id expected"
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        form = self.browse(cr, uid, wiz_id, context)

        if not form.line_ids:
            raise orm.except_orm(_('Error'), _('No credit control lines selected.'))

        line_ids = [l.id for l in form.line_ids]

        filtered_ids = self._filter_line_ids(cr, uid, line_ids, context)
        if not filtered_ids:
            raise except_osv(_('Information'),
                             _('No lines will be changed. All the selected lines are already done.'))

        self._mark_lines(cr, uid, filtered_ids, form.name, context)

        return  {'domain': unicode([('id', 'in', filtered_ids)]),
                 'view_type': 'form',
                 'view_mode': 'tree,form',
                 'view_id': False,
                 'res_model': 'credit.control.line',
                 'type': 'ir.actions.act_window'}

