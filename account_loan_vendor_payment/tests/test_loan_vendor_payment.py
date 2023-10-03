# Copyright 2023 Nextev
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime

from odoo.tests import SavepointCase
from odoo.tests.common import Form


class TestLoanVendorPayment(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountMove = cls.env["account.move"]
        cls.AccountTax = cls.env["account.tax"]

        cls.company = cls.env.ref("base.main_company")
        cls.outstanding_account_id = cls.env["account.account"].create(
            {
                "code": "511500",
                "name": "Check deposis waiting for credit on bank account - (test)",
                "reconcile": True,
                "user_type_id": cls.env.ref(
                    "account.data_account_type_current_assets"
                ).id,
                "company_id": cls.company.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "type": "purchase",
                "name": "Debts",
                "code": "DBT",
                "payment_credit_account_id": cls.outstanding_account_id.id,
                "payment_debit_account_id": cls.outstanding_account_id.id,
            }
        )
        cls.loan_journal = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "type": "purchase",
                "name": "Loan Journal",
                "code": "DBT",
                "payment_credit_account_id": cls.outstanding_account_id.id,
                "payment_debit_account_id": cls.outstanding_account_id.id,
            }
        )
        cls.register_payments_model = cls.env["account.payment.register"]

        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )

        cls.partner = cls.env["res.partner"].create({"name": "Partner Test"})

        cls.account_type = cls.env["account.account.type"].create(
            {
                "name": "acc type test 2",
                "type": "other",
                "include_initial_balance": True,
                "internal_group": "asset",
            }
        )

        cls.account_account_line = cls.env["account.account"].create(
            {
                "name": "acc inv line test",
                "code": "X2021",
                "user_type_id": cls.account_type.id,
                "reconcile": True,
            }
        )

        cls.tax = cls.AccountTax.create(
            {
                "name": "TAX 15%",
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "amount": 15.0,
            }
        )

    def create_post_purchase_invoice(self, amount):
        invoice_form = Form(
            self.AccountMove.with_context(
                default_move_type="in_invoice",
                default_journal_id=self.journal.id,
            )
        )
        invoice_form.partner_id = self.partner

        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "Line 1"
            line_form.quantity = 1
            line_form.price_unit = amount
            line_form.account_id = self.account_account_line
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax)
        invoice = invoice_form.save()
        invoice.invoice_date = datetime.now()
        invoice.action_post()
        return invoice

    def create_loan_payment(self, ctx):
        register_payments = self.register_payments_model.with_context(ctx).create(
            {
                "journal_id": self.loan_journal.id,
                "payment_method_id": self.payment_method_manual_in.id,
                "loan_payment": True,
            }
        )
        return register_payments

    def test_loan_vendor_payment(self):
        invoice = self.create_post_purchase_invoice(200)
        ctx = {"active_model": "account.move", "active_ids": [invoice.id]}
        payment = self.create_loan_payment(ctx)
        loan_action = payment.action_create_payments()
        self.assertEqual(
            invoice.amount_total, loan_action["context"]["default_loan_amount"]
        )
        self.assertEqual(invoice.ids, loan_action["context"]["default_move_ids"])
