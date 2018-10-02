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

from openerp import fields, models
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.queue.job import job
    from openerp.addons.connector.session import ConnectorSession
    from openerp.addons.connector.queue.job import OpenERPJobStorage
except ImportError:
    _logger.debug('Can not `import connector`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory

# do a massive write on account moves BLOCK_SIZE at a time
BLOCK_SIZE = 1000


class AccountMove(models.Model):

    """We modify the account move to allow delayed posting."""

    _name = 'account.move'
    _inherit = 'account.move'

    to_post = fields.Boolean(
        'Posting Requested',
        readonly=True,
        help='Check this box to mark the move for batch posting'
    )
    post_job_uuid = fields.Char(
        'UUID of the Job to approve this move'
    )

    def _delay_post_marked(self, eta=None):
        """Create a job for every move marked for posting.

        If some moves already have a job, they are skipped.

        """
        session = ConnectorSession()
        move_ids = self.search([
            ('to_post', '=', True),
            ('post_job_uuid', '=', False),
            ('state', '=', 'draft'),
        ])
        # maybe not creating too many dictionaries will make us a bit faster
        values = {'post_job_uuid': None}
        _logger.info(
            u'{0} jobs for posting moves have been created.'.format(
                len(move_ids)
            )
        )

        for move_id in move_ids:
            job_uuid = validate_one_move.delay(
                session,
                self._name,
                move_id,
                eta=eta)
            values['post_job_uuid'] = job_uuid
            move_id.write(values)

    def _cancel_jobs(self):
        """Find moves where the mark has been removed and cancel the jobs.
        For the moves that are posted already it's too late: we skip them.
        """
        session = ConnectorSession()
        storage = OpenERPJobStorage(session)

        move_ids = self.search([
            ('to_post', '=', False),
            ('post_job_uuid', '!=', False),
            ('state', '=', 'draft'),
        ])

        for move in move_ids:
            job_rec = storage.load(move.post_job_uuid)
            if job_rec.state in (u'pending', u'enqueued'):
                job_rec.set_done(result=_(
                    u'Task set to Done because the user unmarked the move'
                ))
                storage.store(job_rec)

    def mark_for_posting(self, move_ids, eta=None):
        """Mark a list of moves for delayed posting, and enqueue the jobs."""
        # For massive amounts of moves, this becomes necessary to avoid
        # MemoryError's

        _logger.info(
            u'{0} moves marked for posting.'.format(len(move_ids))
        )

        for start in xrange(0, len(move_ids), BLOCK_SIZE):
            move_ids[start:start + BLOCK_SIZE].write({'to_post': True})
        self._delay_post_marked(eta=eta)

    def unmark_for_posting(self, move_ids):
        """Unmark moves for delayed posting, and cancel the jobs."""
        move_ids.write({'to_post': False})
        self._cancel_jobs()


@job(default_channel='root.AccountMove_batch_validate')
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
