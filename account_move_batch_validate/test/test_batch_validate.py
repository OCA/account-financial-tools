# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA

from openerp.tests.common import TransactionCase
from openerp import fields
from openerp.addons.connector.queue.job import OpenERPJobStorage
from openerp.addons.connector.session import ConnectorSession


class TestBatchValidate(TransactionCase):

    def setUp(self):
        super(TestBatchValidate, self).setUp()

        self.all_journal = self.env['account.journal'].search([])
        self.all_account = self.env['account.account'].search([])

    def _process_job_manually(self, move, del_move=False, test_done=False):

        uuid = move.post_job_uuid

        if del_move:
            self.assertTrue(uuid, 'The Job has not been created.')
            move.unlink()

        session = ConnectorSession.from_env(self.env)
        storage = OpenERPJobStorage(session)

        job = storage.load(uuid)
        if test_done:
            self.assertEqual(
                job.state,
                'done',
                'Job is in state {0}, should be done'.format(job.state)
            )
        else:
            job.perform(session)

        return job

    def test_batch_validate(self):

        self.assertGreater(len(self.all_journal), 0, 'No Journal found!')
        self.assertGreater(len(self.all_journal), 0, 'No Account found!')

        vals_move = {
            'journal_id': self.all_journal[0].id,
            'line_ids': {
                'account_id': self.all_account[0].id,
                'name': 'JOURNAL ITEM LABEL',
            }
        }

        move1 = self.env['account.move'].create(vals_move)

        self.assertEqual(move1.state, 'draft', 'Move in wrong state')

        vals_wizard = {
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today(),
            'action': 'mark',
        }
        wiz_marker1 = self.env['validate.account.move'].create(vals_wizard)
        wiz_marker1.with_context(
            automated_test_execute_now=True
        ).validate_move()
        self._process_job_manually(move1)

        self.assertEqual(move1.state, 'posted', 'Move in wrong state')

        if len(self.all_journal) >= 2:
            journal_0_id = self.all_journal[0].id
            journal_1_id = self.all_journal[1].id
            vals_move = {
                'journal_id': journal_0_id,
                'line_ids': {
                    'account_id': self.all_account[0].id,
                    'name': 'JOURNAL ITEM LABEL',
                }
            }
            move2 = self.env['account.move'].create(vals_move)

            self.assertEqual(move2.state, 'draft', 'Move in wrong state')

            vals_move = {
                'journal_id': journal_1_id,
                'line_ids': {
                    'account_id': self.all_account[0].id,
                    'name': 'JOURNAL ITEM LABEL',
                }
            }
            move3 = self.env['account.move'].create(vals_move)

            self.assertEqual(move3.state, 'draft', 'Move in wrong state')

            vals_wizard = {
                'journal_ids': [(6, 0, [journal_1_id])],
                'date_start': fields.Date.today(),
                'date_end': fields.Date.today(),
                'action': 'mark',
            }
            wiz_marker1 = self.env['validate.account.move'].create(vals_wizard)
            wiz_marker1.with_context(
                automated_test_execute_now=True
            ).validate_move()
            self._process_job_manually(move3)

            self.assertEqual(move2.state, 'draft', 'Move in wrong state')
            self.assertEqual(move3.state, 'posted', 'Move in wrong state')

    def test_batch_validate_then_delete_move(self):
        self.assertGreater(len(self.all_journal), 0, 'No Journal found!')
        self.assertGreater(len(self.all_journal), 0, 'No Account found!')
        vals_move = {
            'journal_id': self.all_journal[0].id,
            'line_ids': {
                'account_id': self.all_account[0].id,
                'name': 'JOURNAL ITEM LABEL',
            }
        }
        move1 = self.env['account.move'].create(vals_move)

        self.assertEqual(move1.state, 'draft', 'Move in wrong state')

        vals_wizard = {
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today(),
            'action': 'mark',
            'eta': 10000,
        }
        wiz_marker1 = self.env['validate.account.move'].create(vals_wizard)
        wiz_marker1.with_context(
            automated_test_execute_now=True
        ).validate_move()
        job = self._process_job_manually(move1, del_move=True)

        self.assertEqual(job.result,
                         'Nothing to do because the record has been deleted')

    def test_batch_validate_then_unmark(self):
        self.assertGreater(len(self.all_journal), 0, 'No Journal found!')
        self.assertGreater(len(self.all_journal), 0, 'No Account found!')
        vals_move = {
            'journal_id': self.all_journal[0].id,
            'line_ids': {
                'account_id': self.all_account[0].id,
                'name': 'JOURNAL ITEM LABEL',
            }
        }
        move1 = self.env['account.move'].create(vals_move)

        self.assertEqual(move1.state, 'draft', 'Move in wrong state')

        vals_wizard = {
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today(),
            'action': 'mark',
            'eta': 10000,
        }
        wiz_marker1 = self.env['validate.account.move'].create(vals_wizard)
        wiz_marker1.with_context(
            automated_test_execute_now=True
        ).validate_move()
        vals_wizard = {
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today(),
            'action': 'unmark',
        }
        wiz_marker2 = self.env['validate.account.move'].create(vals_wizard)
        wiz_marker2.with_context(
            automated_test_execute_now=True
        ).validate_move()
        self._process_job_manually(move1, test_done=True)

        self.assertEqual(move1.state, 'draft', 'Move in wrong state')
