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
import base64

from openerp.osv.orm import  TransientModel, fields
from openerp.osv.osv import except_osv
from openerp.tools.translate import _

class CreditControlPrinter(TransientModel):
    """Change the state of lines in mass"""

    _name = "credit.control.printer"
    _rec_name = 'id'
    _description = """Mass printer"""
    _columns = {'mark_as_sent': fields.boolean('Mark lines as send',
                                               help="Lines to emailed will be ignored"),
                'print_all': fields.boolean('Print all ready lines'),
                'report_file': fields.binary('Generated Report'),
                'state': fields.char('state', size=32)}

    def _get_lids(self, cursor, uid, print_all, active_ids, context=None):
        """get line to be marked filter done lines"""
        # TODO Dry with mailer maybe in comm
        line_obj = self.pool.get('credit.control.line')
        if print_all:
            domain = [('state', '=', 'to_be_sent'),
                      ('canal', '=', 'manual')]
        else:
            domain = [('state', '=', 'to_be_sent'),
                      ('id', 'in', active_ids),
                      ('canal', '=', 'manual')]
        return line_obj.search(cursor, uid, domain, context=context)


    def print_lines(self, cursor, uid, wiz_id, context=None):
        comm_obj = self.pool.get('credit.control.communication')
        context = context or {}
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        current = self.browse(cursor, uid, wiz_id, context)
        lines_ids = context.get('active_ids')
        if not lines_ids and not current.print_all:
            raise except_osv(_('Not lines ids are selected'),
                             _('You may check "Print all ready lines"'))
        if current.print_all:
            filtered_ids = self._get_lids(cursor, uid, current.print_all, lines_ids, context)
        else:
            filtered_ids = lines_ids
        comms = comm_obj._generate_comm_from_credit_line_ids(cursor, uid, filtered_ids,
                                                             context=context)
        report_file = comm_obj._generate_report(cursor, uid, comms, context=context)
        current.write({'report_file': base64.b64encode(report_file), 'state': 'done'})
        if current.mark_as_sent:
            filtered_ids = self._get_lids(cursor, uid, False, lines_ids, context)
            comm_obj._mark_credit_line_as_sent(cursor, uid, comms, context=context)
        return False
