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

from openerp.tools.translate import _
from openerp import exceptions
from openerp.osv import orm, fields

SYNC_OR_ASYNC_ERR_MSG = _('You must choose between sync or async post '
                          'for manual entries')


class AccountJournal(orm.Model):
    _inherit = 'account.journal'

    _columns = {
        'entry_posted_async': fields.boolean(
            'Asynchronously Post for Manual Entries',
            help='Check this box if you don\'t want new journal entries to '
                 'be posted asynchronously  without any manual validation. \n'
                 'Note that journal entries are posted sequentially to avoid '
                 'concurrent update on ir_sequence'),
    }

    def create(self, cr, user, vals, context=None):
        if (vals.get('entry_posted') and
                vals.get('entry_posted_async')):
            raise exceptions.Warning(SYNC_OR_ASYNC_ERR_MSG)
        return orm.Model.create(self, cr, user, vals, context=context)

    def write(self, cr, user, ids, vals, context=None):
        res = orm.Model.write(self, cr, user, ids, vals, context=context)
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for info in self.read(
                cr, user, ids, ['entry_posted', 'entry_posted_async'],
                context=context):
            if (info.get('entry_posted') and
                    info.get('entry_posted_async')):
                raise exceptions.Warning(SYNC_OR_ASYNC_ERR_MSG)
        return res

    def on_change_entry_posted(self, cr, uid, ids, boolval):
        value = {}
        res = {'value': value}
        if boolval:
            value['entry_posted_async'] = False
        return res

    def on_change_entry_posted_async(self, cr, uid, ids, boolval):
        value = {}
        res = {'value': value}
        if boolval:
            value['entry_posted'] = False
        return res
