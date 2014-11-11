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


class AccountBankStatementLine(orm.Model):
    _inherit = "account.bank.statement.line"

    def process_reconciliation(self, cr, uid, id, mv_line_dicts, context=None):
        """Add the from_parent_object key in context in order to be able
        to post the move.
        """
        if context is None:
            context = {}
        else:
            context = context.copy()
        context['from_parent_object'] = True
        _super = super(AccountBankStatementLine, self)
        return _super.process_reconciliation(cr, uid, id, mv_line_dicts,
                                             context=context)
