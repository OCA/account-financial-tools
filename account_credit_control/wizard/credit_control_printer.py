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
import base64

from openerp.osv.orm import  TransientModel, fields
from openerp.osv.osv import except_osv
from openerp.tools.translate import _

class CreditControlPrinter(TransientModel):
    """Print lines"""

    _name = "credit.control.printer"
    _rec_name = 'id'
    _description = 'Mass printer'

    def _get_line_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = False
        if (context.get('active_model') == 'credit.control.line' and
                context.get('active_ids')):
            res = context['active_ids']
        return res

    _columns = {
        'mark_as_sent': fields.boolean('Mark letter lines as sent',
                                       help="Only letter lines will be marked."),
        'print_all': fields.boolean('Print all "Ready To Send" lines of the "Letter" channel'),
        'report_file': fields.binary('Generated Report', readonly=True),
        'state': fields.char('state', size=32),
        'line_ids': fields.many2many(
            'credit.control.line',
            string='Credit Control Lines'),
    }

    _defaults = {
        'mark_as_sent': True,
        'line_ids': _get_line_ids,
    }

    def _filter_line_ids(self, cr, uid, print_all, active_ids, context=None):
        """filter lines to use in the wizard"""
        line_obj = self.pool.get('credit.control.line')
        if print_all:
            domain = [('state', '=', 'to_be_sent'),
                      ('channel', '=', 'letter')]
        else:
            domain = [('state', '=', 'to_be_sent'),
                      ('id', 'in', active_ids),
                      ('channel', '=', 'letter')]
        return line_obj.search(cr, uid, domain, context=context)

    def print_lines(self, cr, uid, wiz_id, context=None):
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
                "wiz_id: only one id expected"
        comm_obj = self.pool.get('credit.control.communication')
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        form = self.browse(cr, uid, wiz_id, context)

        if not form.line_ids and not form.print_all:
            raise except_osv(_('Error'), _('No credit control lines selected.'))

        line_ids = [l.id for l in form.line_ids]
        if form.print_all:
            filtered_ids = self._filter_line_ids(
                cr, uid, form.print_all, line_ids, context)
        else:
            filtered_ids = line_ids
        comms = comm_obj._generate_comm_from_credit_line_ids(
                cr, uid, filtered_ids, context=context)
        report_file = comm_obj._generate_report(cr, uid, comms, context=context)

        form.write({'report_file': base64.b64encode(report_file), 'state': 'done'})

        if form.mark_as_sent:
            filtered_ids = self._filter_line_ids(cr, uid, False, line_ids, context)
            comm_obj._mark_credit_line_as_sent(cr, uid, comms, context=context)

        return False  # do not close the window, we need it to download the report

