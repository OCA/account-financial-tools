# -*- coding: utf-8 -*-
# © 2017 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.osv import orm


class AccountBankStatementLine(orm.Model):
    _inherit = 'account.bank.statement.line'

    def cancel(self, cr, uid, ids, context=None):
        """Override the method to add the key 'from_parent_object' in
        the context. This is to allow to delete move line related to
        bank statement line through the cancel icon.
        """
        context = context and context.copy() or {}
        context['from_parent_object'] = True
        return super(AccountBankStatementLine, self).cancel(
            cr, uid, ids, context=context
        )
