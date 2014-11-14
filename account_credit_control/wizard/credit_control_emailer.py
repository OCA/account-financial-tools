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


class CreditControlEmailer(orm.TransientModel):

    """Send emails for each selected credit control lines."""

    _name = "credit.control.emailer"
    _description = """Mass credit line emailer"""
    _rec_name = 'id'

    def _get_line_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = False
        if (context.get('active_model') == 'credit.control.line' and
                context.get('active_ids')):
            res = self._filter_line_ids(
                cr, uid,
                context['active_ids'],
                context=context
            )
        return res

    _columns = {
        'line_ids': fields.many2many(
            'credit.control.line',
            string='Credit Control Lines',
            domain=[('state', '=', 'to_be_sent'),
                    ('channel', '=', 'email')]
        ),
    }

    _defaults = {
        'line_ids': _get_line_ids,
    }

    def _filter_line_ids(self, cr, uid, active_ids, context=None):
        """filter lines to use in the wizard"""
        line_obj = self.pool.get('credit.control.line')
        domain = [('state', '=', 'to_be_sent'),
                  ('id', 'in', active_ids),
                  ('channel', '=', 'email')]
        return line_obj.search(cr, uid, domain, context=context)

    def email_lines(self, cr, uid, wiz_id, context=None):
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
            "wiz_id: only one id expected"
        comm_obj = self.pool.get('credit.control.communication')
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        form = self.browse(cr, uid, wiz_id, context)

        if not form.line_ids:
            raise orm.except_orm(
                _('Error'),
                _('No credit control lines selected.')
            )

        line_ids = [l.id for l in form.line_ids]
        filtered_ids = self._filter_line_ids(
            cr, uid, line_ids, context
        )
        comms = comm_obj._generate_comm_from_credit_line_ids(
            cr, uid, filtered_ids, context=context
        )
        comm_obj._generate_emails(cr, uid, comms, context=context)
        return {}
