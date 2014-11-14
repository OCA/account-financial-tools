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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class CreditControlPrinter(orm.TransientModel):

    """Print lines"""

    _name = "credit.control.printer"
    _rec_name = 'id'
    _description = 'Mass printer'

    def _get_line_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = False
        if context.get('active_model') != 'credit.control.line':
            return res
        res = context.get('active_ids', False)
        return res

    _columns = {
        'mark_as_sent': fields.boolean(
            'Mark letter lines as sent',
            help="Only letter lines will be marked."
        ),
        'report_file': fields.binary('Generated Report', readonly=True),
        'report_name': fields.char('Report name'),
        'state': fields.char('state', size=32),
        'line_ids': fields.many2many(
            'credit.control.line',
            string='Credit Control Lines'),
    }

    _defaults = {
        'mark_as_sent': True,
        'line_ids': _get_line_ids,
    }

    def _filter_line_ids(self, cr, uid, active_ids, context=None):
        """filter lines to use in the wizard"""
        line_obj = self.pool.get('credit.control.line')
        domain = [('state', '=', 'to_be_sent'),
                  ('id', 'in', active_ids),
                  ('channel', '=', 'letter')]
        return line_obj.search(cr, uid, domain, context=context)

    def _credit_line_predicate(self, cr, uid, line_record, context=None):
        return True

    def _get_line_ids(self, cr, uid, lines, predicate, context=None):
        return [l.id for l in lines if predicate(cr, uid, l, context)]

    def print_lines(self, cr, uid, wiz_id, context=None):
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
            "wiz_id: only one id expected"
        comm_obj = self.pool.get('credit.control.communication')
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        form = self.browse(cr, uid, wiz_id, context)

        if not form.line_ids and not form.print_all:
            raise orm.except_orm(_('Error'),
                                 _('No credit control lines selected.'))

        line_ids = self._get_line_ids(cr,
                                      uid,
                                      form.line_ids,
                                      self._credit_line_predicate,
                                      context=context)

        comms = comm_obj._generate_comm_from_credit_line_ids(cr, uid, line_ids,
                                                             context=context)
        report_file = comm_obj._generate_report(cr, uid, comms,
                                                context=context)

        form.write({'report_file': base64.b64encode(report_file),
                    'report_name': ('credit_control_esr_bvr_%s.pdf' %
                                    fields.datetime.now()),
                    'state': 'done'})

        if form.mark_as_sent:
            comm_obj._mark_credit_line_as_sent(cr, uid, comms, context=context)

        return {'type': 'ir.actions.act_window',
                'res_model': 'credit.control.printer',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': form.id,
                'views': [(False, 'form')],
                'target': 'new',
                }
