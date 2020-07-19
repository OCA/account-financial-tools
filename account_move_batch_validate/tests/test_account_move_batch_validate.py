# Copyright 2017 ACSONE SA/NV
# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SingleTransactionCase
from odoo.addons.queue_job.job import Job


class TestAccountMoveBatchValidate(SingleTransactionCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.env = self.env(context=dict(
            self.env.context, tracking_disable=True))
        self.AccountObj = self.env['account.account']
        self.AccountJournalObj = self.env['account.journal']
        self.AccountMoveObj = self.env['account.move']
        self.ValidateAccountMoveObj = self.env['validate.account.move']
        self.QueueJobObj = self.env['queue.job']

        self.account_type_recv = self.env.ref(
            'account.data_account_type_receivable')
        self.account_type_rev = self.env.ref(
            'account.data_account_type_revenue')

        self.account_recv = self.AccountObj.create({
            'code': 'RECVT',
            'name': "Receivable (test)",
            'reconcile': True,
            'user_type_id': self.account_type_recv.id,
        })
        self.account_sale = self.AccountObj.create({
            'code': 'SALET',
            'name': "Revenue (sale)",
            'reconcile': True,
            'user_type_id': self.account_type_rev.id,
        })

        self.sales_journal = self.AccountJournalObj.create({
            'name': "Sales journal",
            'code': 'SAJT',
            'type': 'sale',
            'default_credit_account_id': self.account_sale.id,
            'default_debit_account_id': self.account_sale.id,
        })

    def create_account_move(self, amount):
        return self.AccountMoveObj.create({
            'journal_id': self.sales_journal.id,
            'line_ids': [
                (0, 0, {
                    'name': "Receivable line",
                    'account_id': self.account_recv.id,
                    'debit': amount,
                }),
                (0, 0, {
                    'name': "Sales line",
                    'account_id': self.account_type_rev.id,
                    'credit': amount,
                }),
            ]
        })

    def create_move_validate_wizard(self, action, eta=None):
        return self.ValidateAccountMoveObj.create({
            'asynchronous': True,
            'action': action,
            'eta': eta or 0,
        })

    def test_01_wizard_asynchronous_post(self):
        """
        Create a move and call the validate account move wizard to
        post it.
        """
        move = self.create_account_move(1000)

        self.assertEqual(move.state, 'draft')

        wizard = self.create_move_validate_wizard('mark')
        wizard.with_context({
            'active_ids': [move.id],
            'automated_test_execute_now': True,
        }).validate_move()
        move.invalidate_cache()
        job_uuid = move.post_job_uuid

        self.assertTrue(
            move.to_post, msg="Move should be marked as 'to post'.")
        self.assertTrue(
            bool(job_uuid), msg="A job should have been assigned to the move.")

        post_job = Job.load(self.env, job_uuid)
        post_job.perform()

        self.assertEqual(
            move.state, 'posted', msg="Move should be posted.")

    def test_02_delete_move_before_job_run(self):
        """
        Create a move and call the validate account move wizard to
        post it, and then delete the move.
        """
        move = self.create_account_move(3000)

        wizard = self.create_move_validate_wizard('mark', eta=1000)
        wizard.with_context({
            'active_ids': [move.id],
            'automated_test_execute_now': True,
        }).validate_move()
        move.invalidate_cache()
        job_uuid = move.post_job_uuid

        self.assertTrue(
            bool(job_uuid), msg="The job has not been created.")

        move.unlink()

        post_job = Job.load(self.env, job_uuid)
        post_job.perform()

        self.assertEqual(
            post_job.result,
            'Nothing to do because the record has been deleted.')

    def test_03_mark_and_unmark(self):
        """
        Create a move and call the validate account move wizard to
        post it. Recall the validate account move wizard to unmark move.
        """
        move = self.create_account_move(3000)

        wizard = self.create_move_validate_wizard('mark', eta=1000)
        wizard.with_context({
            'active_ids': [move.id],
            'automated_test_execute_now': True,
        }).validate_move()
        move.invalidate_cache()
        mark_job_uuid = move.post_job_uuid

        self.assertTrue(move.to_post)

        wizard = self.create_move_validate_wizard('unmark', eta=1000)
        wizard.with_context({
            'active_ids': [move.id],
            'automated_test_execute_now': True,
        }).validate_move()

        self.assertFalse(move.to_post)

        job_uuid = move.post_job_uuid

        self.assertEqual(mark_job_uuid, job_uuid)

        post_job = Job.load(self.env, job_uuid)

        self.assertEqual(post_job.state, 'done', msg="Job should be done")
        self.assertEqual(
            post_job.result,
            "Task set to Done because the user unmarked the move.")

        self.assertEqual(
            move.state, 'draft', msg="Move should be in 'draft' state")
