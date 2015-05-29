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

from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.connector import install_in_connector

# install the module in connector to register the job function
install_in_connector()


class AccountMove(orm.Model):
    _inherit = 'account.move'

    def button_validate(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        context = context or {}
        session = ConnectorSession(cr, uid, context=context)
        for move in self.browse(cr, uid, ids, context=context):
            if not move.journal_id.entry_posted_async:
                self.do_button_validate(cr, uid, ids, context)
            else:
                description = _('Validate account move %s') % move.name
                validate_one_move.delay(
                    session, move._name, move.id, description=description)
        return True

    def do_button_validate(self, cr, uid, ids, context=None):
        return super(AccountMove, self).button_validate(
            cr, uid, ids, context=context)


@job(default_channel='root.account_move_validate')
def validate_one_move(session, model_name, move_id):
    """Validate a move"""
    move_pool = session.pool['account.move']
    if move_pool.exists(session.cr, session.uid, [move_id]):
        return move_pool.do_button_validate(
            session.cr,
            session.uid,
            [move_id]
        )
    else:
        return _(u'Nothing to do because the record has been deleted')
