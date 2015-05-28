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
from openerp.addons.connector.session import ConnectorSession

from openerp.addons.account_move_batch_validate.account import \
    validate_one_move


class AccountMove(orm.Model):
    _inherit = 'account.move'

    def delay_validate_if_required(self, cr, uid, _id, context=None):
        session = ConnectorSession(cr, uid, context=context)
        record = self.browse(cr, uid, _id, context=context)
        journal = self.pool['account.journal'].browse(
            cr, uid, record.journal_id.id, context)
        if journal.entry_posted_async:
            if not self.validate(cr, uid, [_id], context):
                return
            job_uuid = validate_one_move.delay(session, record.name, _id)
            values = {'post_job_uuid': job_uuid}
            self.write(cr, uid, [_id], values)

    def create(self, cr, uid, vals, context=None):
        move_id = orm.Model.create(self, cr, uid, vals, context=context)
        if vals.get('line_id', False):
            self.delay_validate_if_required(cr, uid, move_id, context)
        return move_id
