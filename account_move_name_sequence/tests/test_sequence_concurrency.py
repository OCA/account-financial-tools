import logging
import threading
import time
from unittest.mock import patch

import psycopg2

from odoo import SUPERUSER_ID, api, fields, tools
from odoo.fields import Domain
from odoo.modules.registry import DummyRLock, Registry
from odoo.tests import Form, TransactionCase, tagged

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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._registry_lock_patcher = patch.object(Registry, "_lock", DummyRLock())
        cls.startClassPatcher(cls._registry_lock_patcher)

        with cls.env.registry.cursor() as cr:
            env = api.Environment(cr, api.SUPERUSER_ID, {})

            Product = env["product.product"]
            Partner = env["res.partner"]
            Sequence = env["ir.sequence"]
            Journal = env["account.journal"]

            product = Product.create({"name": "Test Product"})
            partner = Partner.create({"name": "Test Partner 1"})
            partner2 = Partner.create({"name": "Test Partner 2"})
            date = fields.Date.to_date("1985-04-14")
            journal_sale_seq = Sequence.create(
                {
                    "name": "Standard Sale Sequence Demo",
                    "prefix": "SSS_demo/%(range_year)s/",
                    "use_date_range": True,
                    "number_next": 1,
                    "number_increment": 1,
                    "company_id": env.ref("base.main_company").id,
                    "implementation": "standard",
                }
            )
            journal_sale_std = Journal.create(
                {
                    "name": "Standard Sale Journal Demo",
                    "code": "SSJD",
                    "type": "sale",
                    "refund_sequence": True,
                    "company_id": env.ref("base.main_company").id,
                    "sequence_id": journal_sale_seq.id,
                }
            )
            journal_cash_seq = Sequence.create(
                {
                    "name": "Standard Cash Sequence Demo",
                    "prefix": "SCS_demo/%(range_year)s/",
                    "use_date_range": True,
                    "number_next": 1,
                    "number_increment": 1,
                    "company_id": env.ref("base.main_company").id,
                    "implementation": "standard",
                }
            )
            journal_cash_std = Journal.create(
                {
                    "name": "Standard Cash Journal Demo",
                    "code": "SCJD",
                    "type": "cash",
                    "refund_sequence": True,
                    "company_id": env.ref("base.main_company").id,
                    "sequence_id": journal_cash_seq.id,
                }
            )
            cls.data = {
                "date": date,
                "product_id": product.id,
                "partner_id": partner.id,
                "partner2_id": partner2.id,
                "journal_sale_seq_id": journal_sale_seq.id,
                "journal_cash_seq_id": journal_cash_seq.id,
                "journal_sale_id": journal_sale_std.id,
                "journal_cash_id": journal_cash_std.id,
            }
            env.cr.commit()

        cls.cr0 = cls.registry.cursor()
        cls.env0 = api.Environment(cls.cr0, SUPERUSER_ID, {})
        cls.cr1 = cls.registry.cursor()
        cls.env1 = api.Environment(cls.cr1, SUPERUSER_ID, {})
        cls.cr2 = cls.registry.cursor()
        cls.env2 = api.Environment(cls.cr2, SUPERUSER_ID, {})
        for cr in [cls.cr0, cls.cr1, cls.cr2]:
            # Set a 10-second timeout to avoid waiting too long for release locks
            cr.execute("SET LOCAL statement_timeout = '10s'")
        cls.last_existing_move_id = (
            cls.env["account.move"].search([], limit=1, order="id desc").id or 0
        )
        cls.addClassCleanup(cls._cleanup)

    @classmethod
    def _cleanup(cls):
        with cls.env.registry.cursor() as cr:
            env = api.Environment(cr, api.SUPERUSER_ID, {})
            moves = (
                env["account.move"]
                .with_context(force_delete=True)
                .search(Domain("id", ">", cls.last_existing_move_id))
            )
            payments = moves.payment_ids
            moves_without_payments = moves - payments.move_id
            if payments:
                payments.action_draft()
                payments.unlink()
            if moves_without_payments:
                moves_without_payments.filtered(
                    lambda move: move.state != "draft"
                ).button_draft()
                moves_without_payments.unlink()

            try:
                journals = env["account.journal"].browse(
                    [
                        cls.data["journal_sale_id"],
                        cls.data["journal_cash_id"],
                    ]
                )
                journals.unlink()
            except Exception as e:
                _logger.warning("Failed to delete journals: %s", e)

            try:
                sequences = env["ir.sequence"].browse(
                    [
                        cls.data["journal_sale_seq_id"],
                        cls.data["journal_cash_seq_id"],
                    ]
                )
                sequences.unlink()
            except Exception as e:
                _logger.warning("Failed to delete sequences: %s", e)

            try:
                partners = env["res.partner"].browse(
                    [
                        cls.data["partner_id"],
                        cls.data["partner2_id"],
                    ]
                )
                partners.unlink()
            except Exception as e:
                _logger.warning("Failed to delete partners: %s", e)

            try:
                product = env["product.product"].browse(
                    [
                        cls.data["product_id"],
                    ]
                )
                product.unlink()
            except Exception as e:
                _logger.warning("Failed to delete products: %s", e)
            env.cr.commit()

        for cr in [cls.cr0, cls.cr1, cls.cr2]:
            if not cr.closed:
                try:
                    cr.close()
                except Exception as e:
                    _logger.warning("Failed to close cursor: %s", e)

    def _commit_crs(self, *envs):
        for env in envs:
            env.cr.commit()

    def _create_invoice_form(
        self, env, post=True, partner_id=None, ir_sequence_standard=False
    ):
        ctx = {"default_move_type": "out_invoice"}
        with Form(env["account.move"].with_context(**ctx)) as invoice_form:
            # Use another partner to bypass "increase_rank" lock error
            invoice_form.partner_id = (
                partner_id
                and env["res.partner"].browse(partner_id)
                or env["res.partner"].browse(self.data["partner_id"])
            )
            invoice_form.invoice_date = self.data["date"]

            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = env["product.product"].browse(
                    self.data["product_id"]
                )
                line_form.price_unit = 100.0
                line_form.tax_ids.clear()
            invoice = invoice_form.save()
        if ir_sequence_standard:
            invoice.journal_id = env["account.journal"].browse(
                self.data["journal_sale_id"]
            )
        if post:
            # This patch was added to avoid test failures in the CI pipeline caused by
            # the `account_journal_restrict_mode` module. It avoids errors when setting
            # posted moves to draft and deleting them by bypassing the method that
            # writes the hash field used for validation.
            with patch(
                "odoo.addons.account.models.account_move.AccountMove._hash_moves"
            ):
                invoice.action_post()
        return invoice

    def _create_payment_form(self, env, partner_id=None, ir_sequence_standard=False):
        with Form(
            env["account.payment"].with_context(
                default_payment_type="inbound",
                default_partner_type="customer",
                default_move_journal_types=("bank", "cash"),
            )
        ) as payment_form:
            payment_form.partner_id = (
                partner_id
                and env["res.partner"].browse(partner_id)
                or env["res.partner"].browse(self.data["partner_id"])
            )
            payment_form.amount = 100
            payment_form.date = self.data["date"]
            if ir_sequence_standard:
                payment_form.journal_id = env["account.journal"].browse(
                    self.data["journal_cash_id"]
                )
            payment = payment_form.save()
        # This patch was added to avoid test failures in the CI pipeline caused by
        # the `account_journal_restrict_mode` module. It avoids errors when setting
        # posted moves to draft and deleting them by bypassing the method that
        # writes the hash field used for validation.
        with patch("odoo.addons.account.models.account_move.AccountMove._hash_moves"):
            payment.action_post()
        return payment

    def _create_invoice_payment(
        self, deadlock_timeout, payment_first=False, ir_sequence_standard=False
    ):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            cr_pid = cr.connection.get_backend_pid()
            # Avoid waiting for a long time and it needs to be less than deadlock
            cr.execute("SET LOCAL statement_timeout = '%ss'", (deadlock_timeout + 10,))
            if payment_first:
                _logger.info("[PID %s] Creating payment", cr_pid)
                self._create_payment_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
                _logger.info("[PID %s] Creating invoice", cr_pid)
                self._create_invoice_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
            else:
                _logger.info("[PID %s] Creating invoice", cr_pid)
                self._create_invoice_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
                _logger.info("[PID %s] Creating payment", cr_pid)
                self._create_payment_form(
                    env, ir_sequence_standard=ir_sequence_standard
                )
        # sleep in order to avoid release the locks too faster
        # It could be many methods called after creating these
        # kind of records e.g. reconcile
        _logger.info(
            "[PID %s] Finishing, wait %ss before release", cr_pid, deadlock_timeout + 12
        )
        time.sleep(deadlock_timeout + 12)

    def test_sequence_concurrency_10_draft_invoices(self):
        """Creating 2 DRAFT invoices not should raises errors"""
        # Create "last move" to lock
        self._create_invoice_form(self.env0)
        self.env0.cr.commit()
        invoice1 = self._create_invoice_form(self.env1, post=False)
        self.assertEqual(invoice1.state, "draft")
        invoice2 = self._create_invoice_form(self.env2, post=False)
        self.assertEqual(invoice2.state, "draft")
        self._commit_crs(self.env0, self.env1, self.env2)

    def test_sequence_concurrency_20_editing_last_invoice(self):
        """Edit last invoice and create a new invoice
        should not raises errors"""
        # Create "last move" to lock
        invoice = self._create_invoice_form(self.env0)
        self.env0.cr.commit()
        # Edit something in "last move"
        invoice.write({"write_uid": self.env0.uid})
        self.env0.flush_all()
        self._create_invoice_form(self.env1)
        self._commit_crs(self.env0, self.env1)

    def test_sequence_concurrency_30_editing_last_payment(self):
        """Edit last payment and create a new payment
        should not raises errors"""
        # Create "last move" to lock
        payment = self._create_payment_form(self.env0)
        payment_move = payment.move_id
        self.env0.cr.commit()
        # Edit something in "last move"
        payment_move.write({"write_uid": self.env0.uid})
        self.env0.flush_all()
        self._create_payment_form(self.env1)
        self._commit_crs(self.env0, self.env1)

    @tools.mute_logger("odoo.sql_db")
    def test_sequence_concurrency_40_reconciling_last_invoice(self):
        """Reconcile last invoice and create a new one
        should not raises errors"""
        # Create "last move" to lock
        invoice = self._create_invoice_form(self.env0)
        payment = self._create_payment_form(self.env0)
        payment_move = payment.move_id
        self.env0.cr.commit()
        lines2reconcile = (
            (payment_move | invoice)
            .mapped("line_ids")
            .filtered(lambda line: line.account_id.account_type == "asset_receivable")
        )
        # Reconciling "last move"
        # reconcile a payment with many invoices spend a lot so it could
        # lock records too many time
        lines2reconcile.reconcile()
        # Many pieces of code call flush directly
        self.env0.flush_all()
        self._create_invoice_form(self.env1)
        self._commit_crs(self.env0, self.env1)

    def test_sequence_concurrency_50_reconciling_last_payment(self):
        """Reconcile last payment and create a new one
        should not raises errors"""
        # Create "last move" to lock
        invoice = self._create_invoice_form(self.env0)
        payment = self._create_payment_form(self.env0)
        payment_move = payment.move_id
        self.env0.cr.commit()
        lines2reconcile = (
            (payment_move | invoice)
            .mapped("line_ids")
            .filtered(lambda line: line.account_id.account_type == "asset_receivable")
        )
        # Reconciling "last move"
        # reconcile a payment with many invoices spend a lot so it could
        # lock records too many time
        lines2reconcile.reconcile()
        # Many pieces of code call flush directly
        self.env0.flush_all()
        self._create_payment_form(self.env1)
        self._commit_crs(self.env0, self.env1)

    def test_sequence_concurrency_90_payments(self):
        """Creating concurrent payments should not raises errors"""
        # Create "last move" to lock
        self._create_payment_form(self.env0, ir_sequence_standard=True)
        self.env0.cr.commit()
        self._create_payment_form(self.env1, ir_sequence_standard=True)
        self._create_payment_form(self.env2, ir_sequence_standard=True)
        self._commit_crs(self.env0, self.env1, self.env2)

    def test_sequence_concurrency_92_invoices(self):
        """Creating concurrent invoices should not raises errors"""
        # Create "last move" to lock
        self._create_invoice_form(self.env0, ir_sequence_standard=True)
        self.env0.cr.commit()
        self._create_invoice_form(self.env1, ir_sequence_standard=True)
        # Using another partner to bypass "increase_rank" lock error
        self._create_invoice_form(
            self.env2, partner_id=self.data["partner2_id"], ir_sequence_standard=True
        )
        self._commit_crs(self.env0, self.env1, self.env2)

    @tools.mute_logger("odoo.sql_db")
    def test_sequence_concurrency_95_pay2inv_inv2pay(self):
        """Creating concurrent payment then invoice and invoice then payment
        should not raises errors
        It raises deadlock sometimes"""
        # Create "last move" to lock
        self._create_invoice_form(self.env0)
        # Create "last move" to lock
        self._create_payment_form(self.env0)
        self.env0.cr.commit()
        self.env0.cr.execute(
            "SELECT setting FROM pg_settings WHERE name = 'deadlock_timeout'"
        )
        deadlock_timeout = int(self.env0.cr.fetchone()[0])  # ms
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
