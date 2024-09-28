# Copyright 2014-2016 Akretion - Mourad EL HADJ MIMOUNE
# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountCheckDeposit(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.user.write(
            {
                "company_ids": [Command.link(cls.company.id)],
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.account_model = cls.env["account.account"]
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.currency = cls.company.currency_id
        cls.received_check_account = cls.account_model.create(
            {
                "code": "5112ZZ",
                "name": "Received check - (test)",
                "reconcile": True,
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.check_journal = cls.env["account.journal"].create(
            {
                "name": "Received check",
                "type": "bank",
                "code": "ZZCHK",
                "company_id": cls.company.id,
                "inbound_payment_method_line_ids": [
                    (
                        0,
                        0,
                        {
                            "payment_method_id": cls.env.ref(
                                "account.account_payment_method_manual_in"
                            ).id,
                            "payment_account_id": cls.received_check_account.id,
                        },
                    )
                ],
            }
        )
        cls.company_data["default_journal_bank"].bank_account_id = cls.env[
            "res.partner.bank"
        ].create(
            {
                "acc_number": "SI56 1910 0000 0123 438 584",
                "partner_id": cls.company.partner_id.id,
            }
        )

    def create_invoice(self, amount=100):
        """Returns an open invoice"""
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "currency_id": self.currency.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": [],
                        }
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
                "company_id": self.company.id,
                "journal_id": self.check_journal.id,
                "bank_journal_id": self.company_data["default_journal_bank"].id,
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
        self.assertEqual(
            check_deposit.in_hand_check_account_id, self.received_check_account
        )
        liquidity_aml = check_deposit.move_id.line_ids.filtered(
            lambda r: r.account_id != check_deposit.in_hand_check_account_id
        )
        self.assertAlmostEqual(check_deposit.total_amount, 300)
        self.assertAlmostEqual(liquidity_aml.debit, 300)
        self.assertEqual(check_deposit.move_id.state, "posted")
        self.assertEqual(check_deposit.state, "done")
        res = self.env["ir.actions.report"]._render_qweb_text(
            "account_check_deposit.report_checkdeposit", check_deposit.ids
        )
        self.assertRegex(str(res[0]), "SI56 1910 0000 0123 438 584")
