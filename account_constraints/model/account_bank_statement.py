# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume.
#    Copyright 2012-2014 Camptocamp SA
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


class AccountBankStatement(orm.Model):
    _inherit = "account.bank.statement"

    def button_cancel(self, cr, uid, ids, context=None):
        """Override the method to add the key 'from_parent_object' in
        the context. This is to allow to delete move line related to
        bank statement through the cancel button.
        """
        if context is None:
            context = {}
        else:
            context = context.copy()
        context['from_parent_object'] = True
        return super(AccountBankStatement, self).button_cancel(cr, uid, ids,
                                                               context=context)

    def create_move_from_st_line(self, cr, uid, st_line_id,
                                 company_currency_id,
                                 st_line_number, context=None):
        """Add the from_parent_object key in context in order to be able
        to post the move.
        """
        if context is None:
            context = {}
        else:
            context = context.copy()
        context['from_parent_object'] = True
        return super(AccountBankStatement, self).create_move_from_st_line(
            cr, uid, st_line_id, company_currency_id,
            st_line_number, context=context
        )
