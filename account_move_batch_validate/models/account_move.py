# -*- coding: utf-8 -*-
# Copyright 2014 Camptocamp SA, 2017 ACSONE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job, Job


_logger = logging.getLogger(__name__)

BLOCK_SIZE = 1000


class AccountMove(models.Model):

    _inherit = 'account.move'

    to_post = fields.Boolean(
        string="Posting requested", readonly=True,
        help="Check this box to mark the move for batch posting")
    post_job_uuid = fields.Char(string="UUID of the Job to approve this move")

    @job(default_channel='root.account_move_batch_validate')
    def validate_one_move(self, move_id):
        move = self.browse(move_id)
        if move.exists():
            move.post()
        else:
            return _(u"Nothing to do because the record has been deleted")

    @api.model
    def _delay_post_marked(self, eta=None):
        """
        Create a job for every move marked for posting.
        If some moves already have a job, they are skipped.
        """
        AccountMoveObj = self.env[self._name]

        moves = self.search([
            ('to_post', '=', True),
            ('post_job_uuid', '=', False),
            ('state', '=', 'draft'),
        ])

        # maybe not creating too many dictionaries will make us a bit faster
        values = {'post_job_uuid': None}
        _logger.info(
            "%s jobs for posting moves have been created.", len(moves))

        for move in moves:
            new_job = AccountMoveObj.with_delay(eta=eta).validate_one_move(
                move.id)
            values['post_job_uuid'] = new_job.uuid
            move.write(values)
            self.env.cr.commit()  # pylint:disable=invalid-commit

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

        values = {'to_post': True}

        for index in xrange(0, moves_count, BLOCK_SIZE):
            moves = self[index:index + BLOCK_SIZE]
            moves.write(values)
            # users like to see the flag sooner rather than later
            self.env.cr.commit()  # pylint:disable=invalid-commit
        self._delay_post_marked(eta=eta)

    @api.multi
    def unmark_for_posting(self):
        self.write({'to_post': False})
        self._cancel_post_jobs()
