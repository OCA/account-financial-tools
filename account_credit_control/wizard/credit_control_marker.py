# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
from openerp.osv.orm import  TransientModel, fields
from openerp.osv.osv import except_osv
from openerp.tools.translate import _

class CreditControlMarker(TransientModel):
    """Change the state of lines in mass"""

    _name = "credit.control.marker"
    _description = """Mass marker"""
    _columns = {'name': fields.selection([('to_be_sent', 'To send'),
                                          ('sent', 'Done')],
                                          'Mark as', required=True),

                'mark_all': fields.boolean('Change status of all draft lines')}

    _defaults = {'name': 'to_be_sent'}

    def _get_lids(self, cursor, uid, mark_all, active_ids, context=None):
        """get line to be marked filter done lines"""
        line_obj = self.pool.get('credit.control.line')
        if mark_all:
            domain = [('state', '=', 'draft')]
        else:
            domain = [('state', '!=', 'sent'), ('id', 'in', active_ids)]
        return line_obj.search(cursor, uid, domain, context=context)

    def _mark_lines(self, cursor, uid, filtered_ids, state, context=None):
        """write hook"""
        line_obj = self.pool.get('credit.control.line')
        if not state:
            raise ValueError(_('state can not be empty'))
        line_obj.write(cursor, uid, filtered_ids, {'state': state}, context=context)
        return filtered_ids

    def mark_lines(self, cursor, uid, wiz_id, context=None):
        """Write state of selected credit lines to the one in entry
        done credit line will be ignored"""
        if context is None:
            context = {}
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
                "wiz_id: only one id expected"
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        current = self.browse(cursor, uid, wiz_id, context)
        lines_ids = context.get('active_ids')

        if not lines_ids and not current.mark_all:
            raise except_osv(_('Error'),
                             _('No lines are selected. You may want to activate '
                               '"Change status of all draft lines"'))
        filtered_ids = self._get_lids(cursor, uid, current.mark_all, lines_ids, context)
        if not filtered_ids:
            raise except_osv(_('Information'),
                             _('No lines will be changed. All the selected lines are already done'))

        # hook function a simple write should be enought
        self._mark_lines(cursor, uid, filtered_ids, current.name, context)

        return  {'domain': "[('id','in',%s)]" % (filtered_ids,),
                 'name': _('%s marked line') % (current.name,),
                 'view_type': 'form',
                 'view_mode': 'tree,form',
                 'view_id': False,
                 'res_model': 'credit.control.line',
                 'type': 'ir.actions.act_window'}

