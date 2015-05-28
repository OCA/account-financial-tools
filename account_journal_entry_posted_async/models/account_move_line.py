# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of account_journal_entry_posted_async,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     account_journal_entry_posted_async is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     account_journal_entry_posted_async is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with account_journal_entry_posted_async.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm


class AccountMoveLine(orm.Model):
    _inherit = 'account.move.line'

    def create(self, cr, uid, vals, context=None, check=True):
        context = context or {}
        move_line_id = super(AccountMoveLine, self).create(
            cr, uid, vals, context=context, check=check)
        move_id = vals.get('move_id', False)
        if (check and
            not context.get('novalidate') and
                not context.get('no_store_function')):
            self.pool['account.move'].delay_validate_if_required(
                cr, uid, move_id, context)
        return move_line_id
