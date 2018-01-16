# -*- coding: utf-8 -*-
# Copyright 2014 Leonardo Pistone Camptocamp SA
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import logging

from openerp import fields, models, api
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


class AccountMove(models.Model):
    """We modify the account move to allow delayed posting."""

    _name = 'account.move'
    _inherit = 'account.move'

    to_post = fields.Boolean(
        'Posting Requested',
        readonly=True,
        help='Check this box to mark the move for batch posting',
    )
    post_job_uuid = fields.Char(
        'UUID of the Job to approve this move',
    )

    def _delay_post_marked(self, eta=None):
        """Create a job for every move marked for posting
        If some moves already have a job, they are skipped.
        """

        session = ConnectorSession.from_env(self.env)

        move_ids = self.search([
            ('to_post', '=', True),
            ('post_job_uuid', '=', False),
            ('state', '=', 'draft'),
        ])
        name = self._name

        # maybe not creating too many dictionaries will make us a bit faster
        _logger.info(
            u'{0} jobs for posting moves have been created.'.format(
                len(move_ids)
            )
        )

        for move_id in move_ids:
            job_uuid = validate_one_move.delay(session, name, move_id.id,
                                               eta=eta)
            move_id.write({'post_job_uuid': job_uuid})

    def _cancel_jobs(self):
        """Find moves where the mark has been removed and cancel the jobs.
        For the moves that are posted already it's too late: we skip them.
        """

        session = ConnectorSession.from_env(self.env)
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

    @api.multi
    def mark_for_posting(self, eta=None):
        """Mark a list of moves for delayed posting, and enqueue the jobs."""

        # For massive amounts of moves, this becomes necessary to avoid
        # MemoryError's

        _logger.info(
            u'{0} moves marked for posting.'.format(len(self))
        )

        self.write({'to_post': True})
        # users like to see the flag sooner rather than later
        self._delay_post_marked(eta=eta)

    def unmark_for_posting(self):
        """Unmark moves for delayed posting, and cancel the jobs."""
        self.write({'to_post': False})
        self._cancel_jobs()


@job(default_channel='root.account_move_batch_validate')
def validate_one_move(session, model_name, move_id):
    """Validate a move, and leave the job reference in place."""
    move_ids = session.env[model_name].browse([move_id])
    if move_ids.exists():
        move_ids.post()
    else:
        return _(u'Nothing to do because the record has been deleted')
