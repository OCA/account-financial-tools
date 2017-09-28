# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2012 Camptocamp SA
#    Fabien Moret. Copyright 2017 Martronic SA
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

from openerp import models, api, _
from openerp.exceptions import UserError


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_cancel(self):
        invoices = self.read(['move_id', 'payment_ids'])
        for invoice in invoices:
            if invoice['move_id']:
                # This invoice have a move line, we search move_line
                # concerned by this move
                self._cr.execute("""SELECT po.name as payment_name,
                                     po.date_generated as payment_date,
                                     pl.name
                              FROM account_payment_line as pl
                              INNER JOIN account_payment_order AS po
                              ON po.id = order_id
                              WHERE move_line_id IN (SELECT id
                                                     FROM account_move_line
                                                     WHERE move_id = %s)
                              LIMIT 1""",
                    (invoice['move_id'][0],))
                payment_orders = self._cr.dictfetchone()
                if payment_orders:
                    raise UserError(
                        _("Invoice already imported in the payment "
                          "order (%s) at %s on line %s" %
                          (payment_orders['payment_name'],
                           payment_orders['payment_date'],
                           payment_orders['name']))
                    )
        return super(account_invoice, self).action_cancel()
