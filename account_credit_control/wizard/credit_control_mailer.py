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


class CreditControlMailer(TransientModel):
    """Send emails for each selected credit control lines."""

    _name = "credit.control.mailer"
    _description = """Mass credit line mailer"""
    _rec_name = 'id'

    _columns = {'mail_all': fields.boolean('Send an email for all "To Send" lines.')}


    def _get_lids(self, cursor, uid, mail_all, active_ids, context=None):
        """get line to be marked filter done lines"""
        # TODO DRY with printer
        line_obj = self.pool.get('credit.control.line')
        if mail_all:
            domain = [('state', '=', 'to_be_sent'),
                      ('canal', '=', 'mail')]
        else:
            domain = [('state', '=', 'to_be_sent'),
                      ('id', 'in', active_ids),
                      ('canal', '=', 'mail')]
        return line_obj.search(cursor, uid, domain, context=context)


    def mail_lines(self, cursor, uid, wiz_id, context=None):
        assert not (isinstance(wiz_id, list) and len(wiz_id) > 1), \
                "wiz_id: only one id expected"
        comm_obj = self.pool.get('credit.control.communication')
        if context is None:
            context = {}
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        current = self.browse(cursor, uid, wiz_id, context)
        lines_ids = context.get('active_ids')

        if not lines_ids and not current.mail_all:
            raise except_osv(_('Error'),
                             _('No lines are selected. You may want to activate '
                               '"Send an email for all "To Send" lines."'))

        filtered_ids = self._get_lids(cursor, uid, current.mail_all, lines_ids, context)
        comms = comm_obj._generate_comm_from_credit_line_ids(cursor, uid, filtered_ids,
                                                             context=context)
        comm_obj._generate_mails(cursor, uid, comms, context=context)
        return {}

