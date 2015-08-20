# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Author: Leonardo Pistone
#   Copyright 2014 Camptocamp SA
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
"""Wizards for batch posting."""

import logging

from openerp.osv import fields, orm

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.session import ConnectorSession
    from openerp.addons.connector.queue.job import job
except ImportError:
    _logger.debug('Can not `import connector`.')

    def empty_decorator(func):
        return func
    job = empty_decorator


class ValidateAccountMove(orm.TransientModel):

    """Wizard to mark account moves for batch posting."""

    _inherit = "validate.account.move"

    _columns = {
        'action': fields.selection([('mark', 'Mark for posting'),
                                    ('unmark', 'Unmark for posting')],
                                   "Action", required=True),
        'eta': fields.integer('Seconds to wait before starting the jobs'),
        'asynchronous': fields.boolean('Use asynchronous validation'),
    }

    _defaults = {
        'action': 'mark',
        'asynchronous': True,
    }

    def validate_move(self, cr, uid, ids, context=None):
        """Create a single job that will create one job per move.

        Return action.

        """
        session = ConnectorSession(cr, uid, context=context)
        wizard_id = ids[0]
        # to find out what _classic_write does, read the documentation.
        wizard_data = self.read(cr, uid, wizard_id, context=context,
                                load='_classic_write')
        if not wizard_data.get('asynchronous'):
            return super(ValidateAccountMove, self)\
                .validate_move(cr, uid, ids, context=context)
        wizard_data.pop('id')
        if wizard_data.get('journal_ids'):
            journals_ids_vals = [(6, False,
                                  wizard_data.get('journal_ids'))]
            wizard_data['journal_ids'] = journals_ids_vals
        if wizard_data.get('period_ids'):
            periods_ids_vals = [(6, False,
                                wizard_data.get('period_ids'))]
            wizard_data['period_ids'] = periods_ids_vals

        if context.get('automated_test_execute_now'):
            process_wizard(session, self._name, wizard_data)
        else:
            process_wizard.delay(session, self._name, wizard_data)

        return {'type': 'ir.actions.act_window_close'}

    def process_wizard(self, cr, uid, ids, context=None):
        """Choose the correct list of moves to mark and then validate."""
        for wiz in self.browse(cr, uid, ids, context=context):

            move_obj = self.pool['account.move']

            domain = [('state', '=', 'draft'),
                      ('journal_id', 'in', wiz.journal_ids.ids),
                      ('period_id', 'in', wiz.period_ids.ids)]
            move_ids = move_obj.search(cr, uid, domain, order='date',
                                       context=context)

            if wiz.action == 'mark':
                move_obj.mark_for_posting(cr, uid, move_ids, eta=wiz.eta,
                                          context=context)

            elif wiz.action == 'unmark':
                move_obj.unmark_for_posting(cr, uid, move_ids, context=context)


@job
def process_wizard(session, model_name, wizard_data):
    """Create jobs to validate Journal Entries."""

    wiz_obj = session.pool[model_name]
    new_wiz_id = wiz_obj.create(
        session.cr,
        session.uid,
        wizard_data,
        session.context
    )

    wiz_obj.process_wizard(
        session.cr,
        session.uid,
        ids=[new_wiz_id],
        context=session.context,
    )
