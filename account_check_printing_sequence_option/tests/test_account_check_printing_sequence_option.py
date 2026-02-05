# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command, fields
from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestAccountCheckPrintingSequenceOption(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_id = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.company = cls.env.company

        cls.user_1 = cls.env["res.users"].create(
            {
                "name": "User 1",
                "login": "user1_test",
                "email": "user1@test.com",
                "group_ids": [
                    Command.set([cls.env.ref("account.group_account_user").id])
                ],
            }
        )

        cls.user_2 = cls.env["res.users"].create(
            {
                "name": "User 2",
                "login": "user2_test",
                "email": "user2@test.com",
                "group_ids": [
                    Command.set([cls.env.ref("account.group_account_user").id])
                ],
            }
        )

        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test Check Bank",
                "code": "TCHK",
                "type": "bank",
                "company_id": cls.company.id,
                "check_manual_sequencing": False,
            }
        )

        cls.sequence_user_1 = cls.env["ir.sequence"].create(
            {
                "name": "User 1 Check Sequence",
                "padding": 5,
                "number_next": 1,
            }
        )
        cls.sequence_user_2 = cls.env["ir.sequence"].create(
            {
                "name": "User 2 Check Sequence",
                "padding": 5,
                "number_next": 5,
            }
        )

        cls.sequence_option = cls.env["ir.sequence.option"].create(
            {
                "name": "Test Payment Check Option",
                "model": "account.payment",
                "use_sequence_option": True,
            }
        )

        cls.env["ir.sequence.option.line"].create(
            {
                "name": "User 1 Payment Option",
                "base_id": cls.sequence_option.id,
                "sequence_id": cls.sequence_user_1.id,
                "filter_domain": f"[('create_uid','=',{cls.user_1.id})]",
            }
        )
        cls.env["ir.sequence.option.line"].create(
            {
                "name": "User 2 Payment Option",
                "base_id": cls.sequence_option.id,
                "sequence_id": cls.sequence_user_2.id,
                "filter_domain": f"[('create_uid','=',{cls.user_2.id})]",
            }
        )

    @classmethod
    def _create_invoice(self, move_type):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type=move_type)
        )
        move_form.partner_id = self.partner_id
        move_form.invoice_date = fields.Date.today()
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "Test label"
            line_form.price_unit = 1.0
        invoice = move_form.save()
        invoice.action_post()
        return invoice

    @classmethod
    def _create_payment(self, invoice, user):
        method_line = self.journal.outbound_payment_method_line_ids.filtered(
            lambda line: line.payment_method_id.code == "check_printing"
        )
        wizard = (
            self.env["account.payment.register"]
            .with_user(user)
            .with_context(active_ids=[invoice.id], active_model="account.move")
            .create(
                {
                    "journal_id": self.journal.id,
                    "payment_method_line_id": method_line.id,
                    "payment_date": fields.Date.today(),
                    "amount": invoice.amount_total,
                }
            )
        )
        res = wizard.action_create_payments()
        payments = self.env["account.payment"].browse(res.get("res_id") or [])

        return payments

    def test_each_user_gets_own_sequence(self):
        """Tests that each user gets their own check sequence"""
        # Mock 'do_print_checks' to bypass PDF generation and layout validation.
        # This avoids dependencies on localization modules (e.g., l10n_us) while
        # allowing us to verify the sequence logic that runs before the print call
        with patch(
            "odoo.addons.account_check_printing.models.account_payment.AccountPayment.do_print_checks",
            return_value=True,
        ):
            invoice1 = self._create_invoice("in_invoice")
            payment1 = self._create_payment(invoice1, self.user_1)
            payment1.print_checks()
            self.assertEqual(payment1.check_number, "00001")

            invoice2 = self._create_invoice("in_invoice")
            payment2 = self._create_payment(invoice2, self.user_2)
            payment2.print_checks()
            self.assertEqual(payment2.check_number, "00005")

            invoice1b = self._create_invoice("in_invoice")
            payment1b = self._create_payment(invoice1b, self.user_1)
            payment1b.print_checks()
            self.assertEqual(payment1b.check_number, "00002")
