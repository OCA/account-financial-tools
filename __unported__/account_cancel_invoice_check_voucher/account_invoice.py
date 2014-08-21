# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Camptocamp (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Vincent Renaville (Camptocamp)
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

from openerp.tools.translate import _
from openerp.osv import osv, orm


class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def action_cancel(self, cr, uid, ids, context=None):
        invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids'])
        for invoice in invoices:
            if invoice['move_id']:
                # This invoice have a move line, we search move_line concerned
                # by this move
                cr.execute(
                    """
                SELECT abs.name AS statement_name,
                    abs.date AS statement_date,
                    absl.name
                FROM account_bank_statement_line AS absl
                INNER JOIN account_bank_statement AS abs
                    ON absl.statement_id = abs.id
                WHERE EXISTS (SELECT 1
                    FROM account_voucher_line JOIN account_move_line ON
                    (account_voucher_line.move_line_id = account_move_line.id)
                    WHERE voucher_id=absl.voucher_id
                AND account_move_line.move_id = %s )
                           """,
                    (invoice['move_id'][0],)
                )
                statement_lines = cr.dictfetchone()
                if statement_lines:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Invoice already imported in bank statment (%s) '
                          'at %s on line %s'
                          % (statement_lines['statement_name'],
                             statement_lines['statement_date'],
                             statement_lines['name'],)))

        return super(account_invoice, self).action_cancel(cr, uid, ids,
                                                          context=context)
