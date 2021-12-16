# Copyright 2014-2016 Akretion - Mourad EL HADJ MIMOUNE
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPayment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.register_payments_model = self.env["account.payment.register"]
        self.payment_model = self.env["account.payment"]
        self.journal_model = self.env["account.journal"]
        self.account_model = self.env["account.account"]
        self.move_model = self.env["account.move"]
        self.res_partner_bank_model = self.env["res.partner.bank"]
        self.check_deposit_model = self.env["account.check.deposit"]

        self.partner_agrolait = self.env.ref("base.res_partner_2")
        self.main_company = self.env.ref("base.main_company")
        self.currency_id = self.main_company.currency_id.id
        self.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (self.main_company.id, self.currency_id),
        )
        self.product = self.env.ref("product.product_product_4")
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        self.payment_method_manual_out = self.env.ref(
            "account.account_payment_method_manual_out"
        )
        # check if those accounts exist otherwise create them
        self.account_receivable = self.account_model.search(
            [("company_id", "=", self.main_company.id), ("code", "=", "411100")],
            limit=1,
        )

        if not self.account_receivable:
            self.account_receivable = self.account_model.create(
                {
                    "code": "411100",
                    "name": "Debtors - (test)",
                    "reconcile": True,
                    "user_type_id": self.ref("account.data_account_type_receivable"),
                    "company_id": self.main_company.id,
                }
            )

        self.account_revenue = self.account_model.search(
            [("code", "=", "707100"), ("company_id", "=", self.main_company.id)],
            limit=1,
        )
        if not self.account_revenue:
            self.account_revenue = self.account_model.create(
                {
                    "code": "707100",
                    "name": "Product Sales - (test)",
                    "user_type_id": self.ref("account.data_account_type_revenue"),
                    "company_id": self.main_company.id,
                }
            )

        self.received_check_account_id = self.account_model.search(
            [("code", "=", "511200"), ("company_id", "=", self.main_company.id)],
            limit=1,
        )
        if self.received_check_account_id:
            if not self.received_check_account_id.reconcile:
                self.received_check_account_id.reconcile = True
        else:
            self.received_check_account_id = self.account_model.create(
                {
                    "code": "511200",
                    "name": "Received check - (test)",
                    "reconcile": True,
                    "user_type_id": self.ref(
                        "account.data_account_type_current_assets"
                    ),
                    "company_id": self.main_company.id,
                }
            )
        self.transfer_account_id = self.account_model.search(
            [("code", "=", "511500"), ("company_id", "=", self.main_company.id)],
            limit=1,
        )
        if not self.transfer_account_id:
            self.transfer_account_id = self.account_model.create(
                {
                    "code": "511500",
                    "name": "Check deposis waiting for credit on bank account - (test)",
                    "reconcile": True,
                    "user_type_id": self.ref(
                        "account.data_account_type_current_assets"
                    ),
                    "company_id": self.main_company.id,
                }
            )

        self.check_journal = self.journal_model.search(
            [("code", "=", "CHK"), ("company_id", "=", self.main_company.id)], limit=1
        )
        if not self.check_journal:
            self.check_journal = self.journal_model.create(
                {
                    "name": "received check",
                    "type": "bank",
                    "code": "CHK",
                    "company_id": self.main_company.id,
                }
            )
        self.check_journal.payment_debit_account_id = self.received_check_account_id
        self.check_journal.payment_credit_account_id = self.received_check_account_id
        self.bank_journal = self.journal_model.search(
            [("code", "=", "BNK1"), ("company_id", "=", self.main_company.id)], limit=1
        )
        if not self.bank_journal:
            self.bank_journal = self.journal_model.create(
                {
                    "name": "Bank",
                    "type": "bank",
                    "code": "BNK1",
                    "company_id": self.main_company.id,
                }
            )
        self.bank_journal.payment_debit_account_id = self.transfer_account_id
        self.bank_journal.payment_credit_account_id = self.transfer_account_id
        self.partner_bank_id = self.res_partner_bank_model.search(
            [("partner_id", "=", self.main_company.partner_id.id)], limit=1
        )
        if not self.partner_bank_id:
            self.partner_bank_id = self.res_partner_bank_model.create(
                {
                    "acc_number": "SI56 1910 0000 0123 438 584",
                    "partner_id": self.main_company.partner_id.id,
                }
            )
        self.bank_journal.bank_account_id = self.partner_bank_id.id

    def create_invoice(self, amount=100, inv_type="out_invoice", currency_id=None):
        """Returns an open invoice"""
        invoice = self.move_model.create(
            {
                "company_id": self.main_company.id,
                "move_type": inv_type,
                "partner_id": self.partner_agrolait.id,
                "currency_id": currency_id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def create_check_deposit(self, move_lines):
        """Returns an validated check deposit"""
        check_deposit = self.check_deposit_model.create(
            {
                "company_id": self.main_company.id,
                "journal_id": self.check_journal.id,
                "bank_journal_id": self.bank_journal.id,
                "currency_id": self.currency_id,
            }
        )
        check_deposit.get_all_checks()
        check_deposit.validate_deposit()
        return check_deposit

    def test_full_payment_process(self):
        """Create a payment for on invoice by check,
        post it and create check deposit"""
        inv_1 = self.create_invoice(amount=100, currency_id=self.currency_id)
        inv_2 = self.create_invoice(amount=200, currency_id=self.currency_id)

        ctx = {"active_model": "account.move", "active_ids": [inv_1.id, inv_2.id]}
        register_payments = self.register_payments_model.with_context(ctx).create(
            {
                "journal_id": self.check_journal.id,
                "payment_method_id": self.payment_method_manual_in.id,
                "group_payment": True,
            }
        )
        register_payments.action_create_payments()
        payment = self.payment_model.search([], order="id desc", limit=1)

        self.assertAlmostEqual(payment.amount, 300)
        self.assertEqual(payment.state, "posted")
        self.assertEqual(inv_1.state, "posted")
        self.assertEqual(inv_2.state, "posted")

        check_aml = payment.move_id.line_ids.filtered(
            lambda r: r.account_id == self.received_check_account_id
        )

        check_deposit = self.create_check_deposit([check_aml])
        liquidity_aml = check_deposit.move_id.line_ids.filtered(
            lambda r: r.account_id == self.transfer_account_id
        )

        self.assertEqual(check_deposit.total_amount, 300)
        self.assertEqual(liquidity_aml.debit, 300)
        self.assertEqual(check_deposit.move_id.state, "posted")
        self.assertEqual(check_deposit.state, "done")
