# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Vincent Renaville
#    Copyright 2014 Camptocamp SA
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
from openerp.osv import orm


class payment_order_create(orm.TransientModel):

    _inherit = 'payment.order.create'

    def create_payment(self, cr, uid, ids, context=None):
        """
        We recreate function to be able set
        'amount_currency': line.amount_residual_currency
        instead of
        'amount_currency': line.amount_to_pay
        To be compliant with multi currency
        Allready corrected in V8 but will not be corrected in V7
        """
        order_obj = self.pool.get('payment.order')
        line_obj = self.pool.get('account.move.line')
        payment_obj = self.pool.get('payment.line')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        line_ids = [entry.id for entry in data.entries]
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}

        payment = order_obj.browse(cr, uid, context['active_id'],
                                   context=context)
        line2bank = line_obj.line2bank(cr, uid, line_ids, None, context)

        # Finally populate the current payment with new lines:
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if payment.date_prefered == "now":
                # no payment date => immediate payment
                date_to_pay = False
            elif payment.date_prefered == 'due':
                date_to_pay = line.date_maturity
            elif payment.date_prefered == 'fixed':
                date_to_pay = payment.date_scheduled
            state = 'normal'
            if line.invoice and line.invoice.reference_type != 'none':
                state = 'structured'
            currency_id = line.invoice.currency_id.id if line.invoice else None
            if not currency_id:
                currency_id = line.journal_id.currency.id
            if not currency_id:
                currency_id = line.journal_id.company_id.currency_id.id
            payment_obj.create(
                cr, uid, {
                    'move_line_id': line.id,
                    'amount_currency': line.amount_residual_currency,
                    'bank_id': line2bank.get(line.id),
                    'order_id': payment.id,
                    'partner_id': line.partner_id.id,
                    'communication': line.ref or '/',
                    'state': state,
                    'date': date_to_pay,
                    'currency': currency_id,
                }, context=context)
        return {'type': 'ir.actions.act_window_close'}
