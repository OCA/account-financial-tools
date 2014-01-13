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
"""Accounting customisation for delayed posting."""

from openerp.osv import fields, orm

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession


class account_move(orm.Model):

    """We modify the account move to allow delayed posting."""

    _name = 'account.move'
    _inherit = 'account.move'

    _columns = {
        'to_post': fields.boolean(
            'To Post',
            help='Check this box to mark the move for batch posting'
        ),
        'post_job_uuid': fields.char(
            'UUID of the Job to approve this move'
        ),
    }

    def _delay_post_marked(self, cr, uid, context=None):
        """Create a job for every move marked for posting.

        If some moves already have a job, they are skipped.

        """

        if context is None:
            context = {}

        session = ConnectorSession(cr, uid, context=context)

        move_ids = self.search(cr, uid, [
            ('to_post', '=', True),
            ('post_job_uuid', '=', False),
            ('state', '=', 'draft'),
        ], context=context)

        for move_id in move_ids:
            job_uuid = validate_one_move.delay(session, self._name, move_id)
            self.write(cr, uid, [move_id], {
                'post_job_uuid': job_uuid
            })

    def mark_for_posting(self, cr, uid, move_ids, context=None):
        """Mark a list of moves for delayed posting, and enqueue the jobs."""
        if context is None:
            context = {}
        self.write(cr, uid, move_ids, {'to_post': True}, context=context)
        self._delay_post_marked(cr, uid, context=context)


@job
def validate_one_move(session, model_name, move_id):
    """Validate a move, and leave the job reference in place."""
    session.pool['account.move'].button_validate(
        session.cr,
        session.uid,
        [move_id]
    )
