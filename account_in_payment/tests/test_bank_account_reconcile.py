import time

from odoo.tests import Form, tagged

from odoo.addons.account_reconcile_oca.tests.test_bank_account_reconcile import (
    TestReconciliationWidget,
)


@tagged("post_install", "-at_install")
class TestReconciliationWidgetExt(TestReconciliationWidget):
    @classmethod
    def _setup_context(cls):
        return {**cls.env.context, "test_get_invoice_in_payment_state": True}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=cls._setup_context())
        cls.acc_bank_stmt_model = cls.env["account.bank.statement"]
        cls.acc_bank_stmt_line_model = cls.env["account.bank.statement.line"]

    # Testing reconcile action
    def test_payment(self):
        inv1 = self.create_invoice(
            currency_id=self.currency_euro_id,
            invoice_amount=100,
            move_type="in_invoice",
        )
        bank_stmt = self.acc_bank_stmt_model.create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.bank_journal_euro.id,
                "date": time.strftime("%Y-07-15"),
                "name": "test",
            }
        )
        bank_stmt_line = self.acc_bank_stmt_line_model.create(
            {
                "name": "testLine",
                "journal_id": self.bank_journal_euro.id,
                "statement_id": bank_stmt.id,
                "amount": -100,
                "date": time.strftime("%Y-07-15"),
            }
        )
        receivable1 = inv1.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        with Form(
            bank_stmt_line,
            view="account_reconcile_oca.bank_statement_line_form_reconcile_view",
        ) as f:
            self.assertFalse(f.can_reconcile)
            f.add_account_move_line_id = receivable1
            self.assertFalse(f.add_account_move_line_id)
            self.assertTrue(f.can_reconcile)
        self.assertEqual(inv1.amount_residual_signed, -100)
        bank_stmt_line.reconcile_bank_line()
        self.assertEqual(inv1.payment_state, "paid")

    def test_in_payment(self):
        inv1 = self.create_invoice(
            currency_id=self.currency_euro_id,
            invoice_amount=100,
            move_type="in_invoice",
        )
        action = inv1.action_register_payment()
        form = Form(
            self.env[action["res_model"]].with_context(
                mail_create_nolog=True, **action["context"]
            )
        )
        payments = form.save()._create_payments()
        self.assertEqual(inv1.payment_state, "in_payment")
        bank_stmt = self.acc_bank_stmt_model.create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "journal_id": self.bank_journal_euro.id,
                "date": time.strftime("%Y-07-15"),
                "name": "test",
            }
        )
        bank_stmt_line = self.acc_bank_stmt_line_model.create(
            {
                "name": "testLine",
                "journal_id": self.bank_journal_euro.id,
                "statement_id": bank_stmt.id,
                "amount": -100,
                "date": time.strftime("%Y-07-15"),
            }
        )
        receivable1 = payments.move_id.line_ids.filtered(
            lambda line: not line.reconciled
        )
        self.assertEqual(inv1.amount_residual_signed, 0)
        with Form(
            bank_stmt_line,
            view="account_reconcile_oca.bank_statement_line_form_reconcile_view",
        ) as f:
            self.assertFalse(f.can_reconcile)
            f.add_account_move_line_id = receivable1
            self.assertFalse(f.add_account_move_line_id)

            self.assertTrue(f.can_reconcile)
        self.assertEqual(inv1.amount_residual_signed, 0)
        self.assertFalse(receivable1.reconciled)
        bank_stmt_line.reconcile_bank_line()
        self.assertEqual(inv1.payment_state, "paid")
        self.assertEqual(inv1.amount_residual_signed, 0)
        self.assertTrue(receivable1.reconciled)
