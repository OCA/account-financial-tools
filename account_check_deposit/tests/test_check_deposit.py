# Copyright 2014-2016 Akretion - Mourad EL HADJ MIMOUNE
# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPayment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.account_model = self.env["account.account"]
        self.partner = self.env["res.partner"].create({"name": "Test partner"})
        self.main_company = self.env.company
        self.currency = self.main_company.currency_id
        self.product = self.env["product.product"].create({"name": "Test product"})
        # check if those accounts exist otherwise create them
        self.account_model.create(
            {
                "code": "411100",
                "name": "Debtors - (test)",
                "reconcile": True,
                "user_type_id": self.ref("account.data_account_type_receivable"),
                "company_id": self.main_company.id,
            }
        )
        self.account_model.create(
            {
                "code": "707100",
                "name": "Product Sales - (test)",
                "user_type_id": self.ref("account.data_account_type_revenue"),
                "company_id": self.main_company.id,
            }
        )
        received_check_account = self.account_model.create(
            {
                "code": "511200",
                "name": "Received check - (test)",
                "reconcile": True,
                "user_type_id": self.ref("account.data_account_type_current_assets"),
                "company_id": self.main_company.id,
            }
        )
        self.transfer_account = self.account_model.create(
            {
                "code": "511500",
                "name": "Check deposis waiting for credit on bank account - (test)",
                "reconcile": True,
                "user_type_id": self.ref("account.data_account_type_current_assets"),
                "company_id": self.main_company.id,
            }
        )
        self.manual_method_in = self.env.ref("account.account_payment_method_manual_in")
        self.check_journal = self._create_journal(
            "received check", "bank", "CHK", received_check_account
        )
        self.bank_journal = self._create_journal(
            "Bank Test Chq", "bank", "TEST@@", self.transfer_account
        )
        self.bank_journal.bank_account_id = self.env["res.partner.bank"].create(
            {
                "acc_number": "SI56 1910 0000 0123 438 584",
                "partner_id": self.main_company.partner_id.id,
            }
        )

    def _create_journal(self, name, journal_type, code, payment_account):
        return self.env["account.journal"].create(
            {
                "name": name,
                "type": journal_type,
                "code": code,
                "company_id": self.main_company.id,
                "inbound_payment_method_line_ids": [
                    (
                        0,
                        0,
                        {
                            "payment_method_id": self.manual_method_in.id,
                            "payment_account_id": payment_account.id,
                        },
                    )
                ],
            }
        )

    def create_invoice(self, amount=100):
        """Returns an open invoice"""
        invoice = self.env["account.move"].create(
            {
                "company_id": self.main_company.id,
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "currency_id": self.currency.id,
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

    def create_check_deposit(self):
        """Returns an validated check deposit"""
        check_deposit = self.env["account.check.deposit"].create(
            {
                "company_id": self.main_company.id,
                "journal_id": self.check_journal.id,
                "bank_journal_id": self.bank_journal.id,
                "currency_id": self.currency.id,
            }
        )
        check_deposit.get_all_checks()
        check_deposit.validate_deposit()
        return check_deposit

    def test_full_payment_process(self):
        """Create a payment for on invoice by check,
        post it and create check deposit"""
        inv_1 = self.create_invoice(amount=100)
        inv_2 = self.create_invoice(amount=200)
        register_payments = (
            self.env["account.payment.register"]
            .with_context(
                active_model="account.move",
                active_ids=[inv_1.id, inv_2.id],
                default_journal_id=self.check_journal.id,
            )
            .create({"group_payment": True})
        )
        payment = register_payments._create_payments()
        self.assertAlmostEqual(payment.amount, 300)
        self.assertEqual(payment.state, "posted")
        check_deposit = self.create_check_deposit()
        liquidity_aml = check_deposit.move_id.line_ids.filtered(
            lambda r: r.account_id == self.transfer_account
        )
        self.assertAlmostEqual(check_deposit.total_amount, 300)
        self.assertAlmostEqual(liquidity_aml.debit, 300)
        self.assertEqual(check_deposit.move_id.state, "posted")
        self.assertEqual(check_deposit.state, "done")
        res = (
            self.env["ir.actions.report"]
            ._get_report_from_name("account_check_deposit.report_checkdeposit")
            ._render_qweb_text(check_deposit.ids, False)
        )
        self.assertRegex(str(res[0]), "SI56 1910 0000 0123 438 584")
