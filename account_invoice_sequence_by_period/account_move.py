# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models


class account_move(models.Model):
    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        if invoice:
            if not invoice.internal_number:
                journal = invoice.journal_id
                if journal.sequence_id:
                    move = invoice.move_id
                    ctx = {
                        'fiscalyear_id': move.period_id.fiscalyear_id.id,
                        'period': move.period_id
                        }
                    number = self.pool['ir.sequence'].next_by_id(
                        cr, uid, journal.sequence_id.id, ctx)
                    invoice.internal_number = number

        return super(account_move, self).post(cr, uid, ids, context=context)
