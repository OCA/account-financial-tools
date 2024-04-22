import logging
import threading
import time

import psycopg2

import odoo
from odoo import SUPERUSER_ID, api, fields, tools
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase

_logger = logging.getLogger(__name__)


class ThreadRaiseJoin(threading.Thread):
    """Custom Thread Class to raise the exception to main thread in the join"""

    def run(self, *args, **kwargs):
        self.exc = None
        try:
            return super().run(*args, **kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, *args, **kwargs):
        res = super().join(*args, **kwargs)
        # Wait for the thread finishes
        while self.is_alive():
            pass
        # raise exception in the join
        # to raise it in the main thread
        if self.exc:
            raise self.exc
        return res


@tagged("post_install", "-at_install", "test_move_sequence")
class TestSequenceConcurrency(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env.ref("product.product_delivery_01")
        self.partner = self.env.ref("base.res_partner_12")
        self.partner2 = self.env.ref("base.res_partner_1")
        self.date = fields.Date.to_date("1985-04-14")
        self.journal_sale_std = self.env.ref(
            "account_move_name_sequence.journal_sale_std_demo"
        )
        self.journal_cash_std = self.env.ref(
            "account_move_name_sequence.journal_cash_std_demo"
        )

    def _new_cr(self):
        return self.env.registry.cursor()

    def _create_invoice_form(
        self, env, post=True, partner=None, ir_sequence_standard=False
    ):
        if partner is None:
            # Use another partner to bypass "increase_rank" lock error
            partner = self.partner
        ctx = {"default_move_type": "out_invoice"}
        with Form(env["account.move"].with_context(**ctx)) as invoice_form:
            invoice_form.partner_id = partner
            invoice_form.invoice_date = self.date

            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
                line_form.price_unit = 100.0
                line_form.tax_ids.clear()
            invoice = invoice_form.save()
        if ir_sequence_standard:
            invoice.journal_id = self.journal_sale_std
        if post:
            invoice.action_post()
        return invoice

    def _create_payment_form(self, env, ir_sequence_standard=False):
        with Form(
            env["account.payment"].with_context(
                default_payment_type="inbound",
                default_partner_type="customer",
                default_move_journal_types=("bank", "cash"),
            )
        ) as payment_form:
            payment_form.partner_id = env.ref("base.res_partner_12")
            payment_form.amount = 100
            payment_form.date = self.date

            payment = payment_form.save()
        if ir_sequence_standard:
            payment.move_id.journal_id = self.journal_cash_std
        payment.action_post()
        return payment

    def _clean_moves(self, move_ids, payment=None):
        """Delete moves created after finish unittest using
        self.addCleanup(
            self._clean_moves, self.env, (invoices | payments.mapped('move_id')).ids
        )"""
        with self._new_cr() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            moves = env["account.move"].browse(move_ids)
            moves.button_draft()
            moves = moves.with_context(force_delete=True)
            moves.unlink()
            # TODO: Delete payment and journal
            env.cr.commit()

    def _create_invoice_payment(
        self, deadlock_timeout, payment_first=False, ir_sequence_standard=False
    ):
        odoo.registry(self.env.cr.dbname)
        with self._new_cr() as cr, cr.savepoint():
            env = api.Environment(cr, SUPERUSER_ID, {})
            cr_pid = cr.connection.get_backend_pid()
            # Avoid waiting for a long time and it needs to be less than deadlock
            cr.execute("SET LOCAL statement_timeout = '%ss'", (deadlock_timeout + 10,))
            if payment_first:
                _logger.info("Creating payment cr %s", cr_pid)
                self._create_payment_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
                _logger.info("Creating invoice cr %s", cr_pid)
                self._create_invoice_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
            else:
                _logger.info("Creating invoice cr %s", cr_pid)
                self._create_invoice_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
                _logger.info("Creating payment cr %s", cr_pid)
                self._create_payment_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
        # sleep in order to avoid release the locks too faster
        # It could be many methods called after creating these
        # kind of records e.g. reconcile
        _logger.info("Finishing waiting %s", (deadlock_timeout + 12))
        time.sleep(deadlock_timeout + 12)

    def test_sequence_concurrency_10_draft_invoices(self):
        """Creating 2 DRAFT invoices not should raises errors"""
        with self._new_cr() as cr0, self._new_cr() as cr1, self._new_cr() as cr2:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})
            env1 = api.Environment(cr1, SUPERUSER_ID, {})
            env2 = api.Environment(cr2, SUPERUSER_ID, {})
            for cr in [cr0, cr1, cr2]:
                # Set 10s timeout in order to avoid waiting for release locks a long time
                cr.execute("SET LOCAL statement_timeout = '10s'")

            # Create "last move" to lock
            invoice = self._create_invoice_form(env0)
            self.addCleanup(self._clean_moves, invoice.ids)
            env0.cr.commit()
            with env1.cr.savepoint(), env2.cr.savepoint():
                invoice1 = self._create_invoice_form(env1, post=False)
                self.assertEqual(invoice1.state, "draft")
                invoice2 = self._create_invoice_form(env2, post=False)
                self.assertEqual(invoice2.state, "draft")

    def test_sequence_concurrency_20_editing_last_invoice(self):
        """Edit last invoice and create a new invoice
        should not raises errors"""
        with self._new_cr() as cr0, self._new_cr() as cr1:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})
            env1 = api.Environment(cr1, SUPERUSER_ID, {})
            for cr in [cr0, cr1]:
                # Set 10s timeout in order to avoid waiting for release locks a long time
                cr.execute("SET LOCAL statement_timeout = '10s'")

            # Create "last move" to lock
            invoice = self._create_invoice_form(env0)

            self.addCleanup(self._clean_moves, invoice.ids)
            env0.cr.commit()
            with env0.cr.savepoint(), env1.cr.savepoint():
                # Edit something in "last move"
                invoice.write({"write_uid": env0.uid})
                env0.flush_all()
                self._create_invoice_form(env1)

    def test_sequence_concurrency_30_editing_last_payment(self):
        """Edit last payment and create a new payment
        should not raises errors"""
        with self._new_cr() as cr0, self._new_cr() as cr1:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})
            env1 = api.Environment(cr1, SUPERUSER_ID, {})
            for cr in [cr0, cr1]:
                # Set 10s timeout in order to avoid waiting for release locks a long time
                cr.execute("SET LOCAL statement_timeout = '10s'")

            # Create "last move" to lock
            payment = self._create_payment_form(env0)
            payment_move = payment.move_id
            self.addCleanup(self._clean_moves, payment_move.ids)
            env0.cr.commit()
            with env0.cr.savepoint(), env1.cr.savepoint():
                # Edit something in "last move"
                payment_move.write({"write_uid": env0.uid})
                env0.flush_all()
                self._create_payment_form(env1)

    @tools.mute_logger("odoo.sql_db")
    def test_sequence_concurrency_40_reconciling_last_invoice(self):
        """Reconcile last invoice and create a new one
        should not raises errors"""
        with self._new_cr() as cr0, self._new_cr() as cr1:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})
            env1 = api.Environment(cr1, SUPERUSER_ID, {})
            for cr in [cr0, cr1]:
                # Set 10s timeout in order to avoid waiting for release locks a long time
                cr.execute("SET LOCAL statement_timeout = '10s'")

            # Create "last move" to lock
            invoice = self._create_invoice_form(env0)
            payment = self._create_payment_form(env0)
            payment_move = payment.move_id
            self.addCleanup(self._clean_moves, invoice.ids + payment_move.ids)
            env0.cr.commit()
            lines2reconcile = (
                (payment_move | invoice)
                .mapped("line_ids")
                .filtered(
                    lambda line: line.account_id.account_type == "asset_receivable"
                )
            )
            with env0.cr.savepoint(), env1.cr.savepoint():
                # Reconciling "last move"
                # reconcile a payment with many invoices spend a lot so it could
                # lock records too many time
                lines2reconcile.reconcile()
                # Many pieces of code call flush directly
                env0.flush_all()
                self._create_invoice_form(env1)

    def test_sequence_concurrency_50_reconciling_last_payment(self):
        """Reconcile last payment and create a new one
        should not raises errors"""
        with self._new_cr() as cr0, self._new_cr() as cr1:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})
            env1 = api.Environment(cr1, SUPERUSER_ID, {})
            for cr in [cr0, cr1]:
                # Set 10s timeout in order to avoid waiting for release locks a long time
                cr.execute("SET LOCAL statement_timeout = '10s'")

            # Create "last move" to lock
            invoice = self._create_invoice_form(env0)
            payment = self._create_payment_form(env0)
            payment_move = payment.move_id
            self.addCleanup(self._clean_moves, invoice.ids + payment_move.ids)
            env0.cr.commit()
            lines2reconcile = (
                (payment_move | invoice)
                .mapped("line_ids")
                .filtered(
                    lambda line: line.account_id.account_type == "asset_receivable"
                )
            )
            with env0.cr.savepoint(), env1.cr.savepoint():
                # Reconciling "last move"
                # reconcile a payment with many invoices spend a lot so it could
                # lock records too many time
                lines2reconcile.reconcile()
                # Many pieces of code call flush directly
                env0.flush_all()
                self._create_payment_form(env1)

    def test_sequence_concurrency_90_payments(self):
        """Creating concurrent payments should not raises errors"""
        with self._new_cr() as cr0, self._new_cr() as cr1, self._new_cr() as cr2:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})
            env1 = api.Environment(cr1, SUPERUSER_ID, {})
            env2 = api.Environment(cr2, SUPERUSER_ID, {})
            for cr in [cr0, cr1, cr2]:
                # Set 10s timeout in order to avoid waiting for release locks a long time
                cr.execute("SET LOCAL statement_timeout = '10s'")

            # Create "last move" to lock
            payment = self._create_payment_form(env0, ir_sequence_standard=True)
            payment_move_ids = payment.move_id.ids
            self.addCleanup(self._clean_moves, payment_move_ids)
            env0.cr.commit()
            with env1.cr.savepoint(), env2.cr.savepoint():
                self._create_payment_form(env1, ir_sequence_standard=True)
                self._create_payment_form(env2, ir_sequence_standard=True)

    def test_sequence_concurrency_92_invoices(self):
        """Creating concurrent invoices should not raises errors"""
        with self._new_cr() as cr0, self._new_cr() as cr1, self._new_cr() as cr2:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})
            env1 = api.Environment(cr1, SUPERUSER_ID, {})
            env2 = api.Environment(cr2, SUPERUSER_ID, {})
            for cr in [cr0, cr1, cr2]:
                # Set 10s timeout in order to avoid waiting for release locks a long time
                cr.execute("SET LOCAL statement_timeout = '10s'")

            # Create "last move" to lock
            invoice = self._create_invoice_form(env0, ir_sequence_standard=True)
            self.addCleanup(self._clean_moves, invoice.ids)
            env0.cr.commit()
            with env1.cr.savepoint(), env2.cr.savepoint():
                self._create_invoice_form(env1, ir_sequence_standard=True)
                # Using another partner to bypass "increase_rank" lock error
                self._create_invoice_form(
                    env2, partner=self.partner2, ir_sequence_standard=True
                )

    @tools.mute_logger("odoo.sql_db")
    def test_sequence_concurrency_95_pay2inv_inv2pay(self):
        """Creating concurrent payment then invoice and invoice then payment
        should not raises errors
        It raises deadlock sometimes"""
        with self._new_cr() as cr0:
            env0 = api.Environment(cr0, SUPERUSER_ID, {})

            # Create "last move" to lock
            invoice = self._create_invoice_form(env0)

            # Create "last move" to lock
            payment = self._create_payment_form(env0)
            payment_move_ids = payment.move_id.ids
            self.addCleanup(self._clean_moves, invoice.ids + payment_move_ids)
            env0.cr.commit()
            env0.cr.execute(
                "SELECT setting FROM pg_settings WHERE name = 'deadlock_timeout'"
            )
            deadlock_timeout = int(env0.cr.fetchone()[0])  # ms
            # You could not have permission to set this parameter
            # psycopg2.errors.InsufficientPrivilege
            self.assertTrue(
                deadlock_timeout,
                "You need to configure PG parameter deadlock_timeout='1s'",
            )
            deadlock_timeout = int(deadlock_timeout / 1000)  # s

            t_pay_inv = ThreadRaiseJoin(
                target=self._create_invoice_payment,
                args=(deadlock_timeout, True, True),
                name="Thread payment invoice",
            )
            t_inv_pay = ThreadRaiseJoin(
                target=self._create_invoice_payment,
                args=(deadlock_timeout, False, True),
                name="Thread invoice payment",
            )
            t_pay_inv.start()
            t_inv_pay.start()
            # the thread could raise the error before to wait for it so disable coverage
            self._thread_join(t_pay_inv, deadlock_timeout + 15)
            self._thread_join(t_inv_pay, deadlock_timeout + 15)

    def _thread_join(self, thread_obj, timeout):
        try:
            thread_obj.join(timeout=timeout)  # pragma: no cover
            self.assertFalse(
                thread_obj.is_alive(),
                "The thread wait is over. but the cursor may still be in use!",
            )
        except psycopg2.OperationalError as e:
            if e.pgcode in [
                psycopg2.errorcodes.SERIALIZATION_FAILURE,
                psycopg2.errorcodes.LOCK_NOT_AVAILABLE,
            ]:  # pragma: no cover
                # Concurrency error is expected but not deadlock so ok
                pass
            elif e.pgcode == psycopg2.errorcodes.DEADLOCK_DETECTED:  # pragma: no cover
                self.assertFalse(True, "Deadlock detected.")
            else:  # pragma: no cover
                raise
