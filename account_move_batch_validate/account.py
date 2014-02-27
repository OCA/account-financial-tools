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

import logging

from openerp.osv import fields, orm
from openerp.tools.translate import _

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import OpenERPJobStorage

_logger = logging.getLogger(__name__)

# do a massive write on account moves BLOCK_SIZE at a time
BLOCK_SIZE = 1000


class account_move(orm.Model):

    """We modify the account move to allow delayed posting."""

    _name = 'account.move'
    _inherit = 'account.move'

    _columns = {
        'to_post': fields.boolean(
            'Posting Requested',
            readonly=True,
            help='Check this box to mark the move for batch posting'
        ),
        'post_job_uuid': fields.char(
            'UUID of the Job to approve this move'
        ),
    }

    def _delay_post_marked(self, cr, uid, eta=None, context=None):
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

        _logger.info(
            u'{0} jobs for posting moves have been created.'.format(
                len(move_ids)
            )
        )

        for move_id in move_ids:
            job_uuid = validate_one_move.delay(session, self._name, move_id,
                                               eta=eta)
            self.write(cr, uid, [move_id], {
                'post_job_uuid': job_uuid
            })

    def _cancel_jobs(self, cr, uid, context=None):
        """Find moves where the mark has been removed and cancel the jobs.

        For the moves that are posted already it's too late: we skip them.

        """

        if context is None:
            context = {}

        session = ConnectorSession(cr, uid, context=context)
        storage = OpenERPJobStorage(session)

        move_ids = self.search(cr, uid, [
            ('to_post', '=', False),
            ('post_job_uuid', '!=', False),
            ('state', '=', 'draft'),
        ], context=context)

        for move in self.browse(cr, uid, move_ids, context=context):
            job = storage.load(move.post_job_uuid)
            if job.state in (u'pending', u'enqueued'):
                job.set_done(result=_(
                    u'Task set to Done because the user unmarked the move'
                ))
                storage.store(job)

    def mark_for_posting(self, cr, uid, move_ids, eta=None, context=None):
        """Mark a list of moves for delayed posting, and enqueue the jobs."""
        if context is None:
            context = {}
        # For massive amounts of moves, this becomes necessary to avoid
        # MemoryError's

        _logger.info(
            u'{0} moves marked for posting.'.format(len(move_ids))
        )

        for start in xrange(0, len(move_ids), BLOCK_SIZE):
            self.write(
                cr,
                uid,
                move_ids[start:start + BLOCK_SIZE],
                {'to_post': True},
                context=context)
        self._delay_post_marked(cr, uid, eta=eta, context=context)

    def unmark_for_posting(self, cr, uid, move_ids, context=None):
        """Unmark moves for delayed posting, and cancel the jobs."""
        if context is None:
            context = {}
        self.write(cr, uid, move_ids, {'to_post': False}, context=context)
        self._cancel_jobs(cr, uid, context=context)


@job
def validate_one_move(session, model_name, move_id):
    """Validate a move, and leave the job reference in place."""
    move_pool = session.pool['account.move']
    if move_pool.exists(session.cr, session.uid, [move_id]):
        move_pool.button_validate(
            session.cr,
            session.uid,
            [move_id]
        )
    else:
        return _(u'Nothing to do because the record has been deleted')
