# Copyright 2014 Camptocamp SA, 2017 ACSONE
# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job, Job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


BLOCK_SIZE = 1000


class AccountMove(models.Model):

    _inherit = 'account.move'

    to_post = fields.Boolean(
        string="Posting requested", readonly=True,
        help="Check this box to mark the move for batch posting")
    post_job_uuid = fields.Char(string="UUID of the Job to approve this move")

    @api.multi
    @job(default_channel='root.account_move_batch_validate')
    def validate_one_move(self):
        if self.exists():
            self.post()
            return _("Move has been posted successfully.")
        else:
            return _("Nothing to do because the record has been deleted.")

    @api.model
    def _delay_post_marked(self, eta=None):
        """
        Create a job for every move marked for posting.
        If some moves already have a job, they are skipped.
        """
        moves = self.search([
            ('to_post', '=', True),
            ('post_job_uuid', '=', False),
            ('state', '=', 'draft'),
        ])

        moves_job_mapping = []
        _logger.info(
            "Creating %s jobs for posting moves.", len(moves))

        for move in moves:
            job = move.with_delay(eta=eta).validate_one_move()
            moves_job_mapping.append((move.id, job.uuid))
        self._update_moves_with_job_uuid(moves_job_mapping)

    @api.model
    def _update_moves_with_job_uuid(self, moves_job_mapping):
        sql = """
            UPDATE account_move AS am
            SET post_job_uuid = v.job_uuid
            FROM (VALUES %s ) AS v (move_id, job_uuid)
            WHERE am.id = v.move_id;
        """
        self.env.cr.execute(sql, tuple(moves_job_mapping))

    @api.model
    def _cancel_post_jobs(self):
        """
        Find moves where the mark has been removed and cancel the jobs.
        For the moves that are posted already it's too late: we skip them.
        """
        moves = self.search([
            ('to_post', '=', False),
            ('post_job_uuid', '!=', False),
            ('state', '=', 'draft'),
        ])

        for move in moves:
            job_rec = Job.load(self.env, move.post_job_uuid)
            if job_rec.state in ('pending', 'enqueued'):
                job_rec.set_done(
                    result=_("Task set to Done because the "
                             "user unmarked the move."))
                job_rec.store()

    @api.multi
    def mark_for_posting(self, eta=None):
        """
        Mark a list of moves for delayed posting, and enqueue the jobs.
        For massive amounts of moves, this becomes necessary to avoid
        MemoryError's
        """
        moves_count = len(self)
        _logger.info("%s moves marked for posting.", moves_count)

        self.write({'to_post': True})
        self._delay_post_marked(eta=eta)

    @api.multi
    def unmark_for_posting(self):
        self.write({'to_post': False})
        self._cancel_post_jobs()
