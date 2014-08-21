# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2012 Camptocamp SA
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

    def action_cancel(self, cr, uid, ids, *args):
        invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids'])
        for invoice in invoices:
            if invoice['move_id']:
                # This invoice have a move line, we search move_line
                # concerned by this move
                cr.execute("""SELECT po.reference as payment_name,
                                     po.date_done as payment_date,
                                     pl.name
                              FROM payment_line as pl
                              INNER JOIN payment_order AS po
                              ON pl.id = order_id
                              WHERE move_line_id IN (SELECT id
                                                     FROM account_move_line
                                                     WHERE move_id = %s)
                              LIMIT 1""",
                           (invoice['move_id'][0],))
                payment_orders = cr.dictfetchone()
                if payment_orders:
                    raise osv.except_osv(
                        _('Error !'),
                        _("Invoice already imported in the payment "
                          "order (%s) at %s on line %s" %
                          (payment_orders['payment_name'],
                           payment_orders['payment_date'],
                           payment_orders['name']))
                    )
        return super(account_invoice, self).action_cancel(cr, uid, ids, *args)
