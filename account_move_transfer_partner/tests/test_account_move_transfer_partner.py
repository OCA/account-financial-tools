# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase

CURRENCY_RATE = 0.5


class TestAccountMoveTransferPartner(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.partner_1 = self.env.ref("base.res_partner_1")
        self.partner_2 = self.env.ref("base.res_partner_2")
        self.partner_3 = self.env.ref("base.res_partner_3")
        self.today = fields.Date.today()

        self.AccountJournal = self.env["account.journal"]
        self.wizard_model = self.env["wizard.account.move.transfer.partner"]
        self.sale_journal = self.AccountJournal.create(
            {
                "name": "Sale journal",
                "code": "SALE",
                "type": "sale",
            }
        )
        self.purchase_journal = self.AccountJournal.create(
            {
                "name": "Purchase journal",
                "code": "PURCHASE",
                "type": "purchase",
            }
        )
        self.general_journal = self.AccountJournal.create(
            {
                "name": "General journal",
                "code": "GENERAL",
                "type": "general",
            }
        )

        self.ProductProduct = self.env["product.product"]
        self.product = self.ProductProduct.create(
            {"name": "Product", "price": 100.0, "standard_price": 100.0}
        )
        charts = self.env["account.chart.template"].search([])
        if charts:
            self.chart = charts[0]
        else:
            raise ValidationError(_("No Chart of Account Template has been defined !"))
        self.AccountMove = self.env["account.move"]
        with Form(
            self.AccountMove.with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = self.today
            invoice_form.partner_id = self.partner_2
            invoice_form.journal_id = self.sale_journal
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
            self.invoice_1 = invoice_form.save()
        self.invoice_2 = self.invoice_1.copy()
        self.invoice_3 = self.invoice_1.copy()
        invoice_form = Form(self.invoice_3)
        invoice_form.partner_id = self.partner_2
        self.invoice_3 = invoice_form.save()
        self.invoice_1.action_post()
        self.invoice_2.action_post()
        self.invoice_3.action_post()

        with Form(
            self.AccountMove.with_context(default_move_type="in_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = self.today
            invoice_form.partner_id = self.partner_1
            invoice_form.journal_id = self.purchase_journal
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
            self.in_invoice = invoice_form.save()
        self.in_invoice.action_post()

        with Form(
            self.AccountMove.with_context(default_move_type="out_refund")
        ) as invoice_form:
            invoice_form.invoice_date = self.today
            invoice_form.partner_id = self.partner_1
            invoice_form.journal_id = self.sale_journal
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
            self.out_refund = invoice_form.save()
        self.out_refund.action_post()
        with Form(
            self.AccountMove.with_context(default_move_type="in_refund")
        ) as invoice_form:
            invoice_form.invoice_date = self.today
            invoice_form.partner_id = self.partner_1
            invoice_form.journal_id = self.purchase_journal
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
            self.in_refund = invoice_form.save()
        self.in_refund.action_post()

        self.general_move = self.AccountMove.create(
            {
                "journal_id": self.general_journal.id,
                "ref": "sample move",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 100.0,
                            "credit": 0,
                            "account_id": self.env["account.account"]
                            .search([("user_type_id.type", "=", "other")], limit=1)
                            .id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 100.0,
                            "account_id": self.env["account.account"]
                            .search([("user_type_id.type", "=", "other")], limit=1)
                            .id,
                        },
                    ),
                ],
            }
        )
        self.general_move.action_post()
        self.payment_term = self.env["account.payment.term"].create(
            {
                "name": "Pay in 2 installments",
                "line_ids": [
                    # Pay 50% immediately
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 50,
                        },
                    ),
                    # Pay the rest after 14 days
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 14,
                        },
                    ),
                ],
            }
        )
        self.currency_2 = self.env["res.currency"].create(
            {
                "name": "test",
                "symbol": "TEST",
                "rate_ids": [
                    (
                        0,
                        0,
                        {
                            "name": fields.Date.today(),
                            "rate": CURRENCY_RATE,
                        },
                    )
                ],
            }
        )
        self.AccountMoveReversal = self.env["account.move.reversal"]

    def test_01_account_move_transfer_partner(self):
        self.assertEqual(self.invoice_1.payment_state, "not_paid")
        self.assertEqual(self.invoice_2.payment_state, "not_paid")
        self.assertEqual(self.invoice_3.payment_state, "not_paid")
        all_invoices = self.invoice_1 + self.invoice_2 + self.invoice_3
        total_residual = sum(i.amount_residual for i in all_invoices)
        wizard_form = Form(
            self.wizard_model.with_context({"active_ids": self.invoice_1.ids})
        )
        self.assertTrue(wizard_form.allow_edit_amount_to_transfer)
        wizard_form.amount_to_transfer = self.invoice_1.amount_residual + 1
        wizard_form.destination_partner_id = self.partner_3
        wizard = wizard_form.save()
        with self.assertRaises(ValidationError):
            wizard.action_create_move()
        wizard.write(
            {
                "amount_to_transfer": 0,
            }
        )
        with self.assertRaises(ValidationError):
            wizard.action_create_move()
        wizard_form = Form(
            self.wizard_model.with_context({"active_ids": all_invoices.ids})
        )
        with self.assertRaises(AssertionError):
            wizard_form.amount_to_transfer = total_residual + 1
        wizard_form.destination_partner_id = self.partner_3
        self.assertFalse(wizard_form.allow_edit_amount_to_transfer)
        wizard = wizard_form.save()
        action = wizard.action_create_move()
        self.assertEqual(self.invoice_1.payment_state, "paid")
        self.assertEqual(self.invoice_2.payment_state, "paid")
        self.assertEqual(self.invoice_3.payment_state, "paid")
        new_moves = action.get("domain", []) and self.AccountMove.browse(
            action.get("domain", [])[0][2]
        )
        unreconciled_lines = new_moves.mapped("line_ids").filtered(
            lambda x: not x.reconciled
        )
        self.assertEqual(
            unreconciled_lines.mapped("partner_id").ids, self.partner_3.ids
        )

    def test_02_account_move_transfer_partner(self):
        wizard_form = Form(
            self.wizard_model.with_context({"active_ids": self.in_invoice.ids})
        )
        self.assertTrue(wizard_form.allow_edit_amount_to_transfer)
        current_residual_amount = self.invoice_1.amount_residual
        wizard_form.amount_to_transfer = current_residual_amount - 1
        wizard_form.destination_partner_id = self.partner_3
        wizard = wizard_form.save()
        action = wizard.action_create_move()
        self.assertEqual(self.in_invoice.amount_residual, 1.0)
        new_moves = action.get("domain", []) and self.AccountMove.browse(
            action.get("domain", [])[0][2]
        )
        partner_1_aml = new_moves.mapped("line_ids").filtered(
            lambda x: x.partner_id.id == self.partner_1.id
        )
        self.assertEqual(abs(partner_1_aml.amount_residual), 0.0)
        partner_3_aml = new_moves.mapped("line_ids").filtered(
            lambda x: x.partner_id.id == self.partner_3.id
        )
        self.assertEqual(
            abs(partner_3_aml.amount_residual), current_residual_amount - 1
        )

    def test_03_account_move_transfer_partner(self):
        wizard_form = Form(
            self.wizard_model.with_context({"active_ids": self.out_refund.ids})
        )
        self.assertTrue(wizard_form.allow_edit_amount_to_transfer)
        wizard_form.destination_partner_id = self.partner_3
        wizard = wizard_form.save()
        wizard.action_create_move()
        self.assertEqual(self.out_refund.amount_residual, 0.0)

    def test_04_account_move_transfer_partner(self):
        wizard_form = Form(
            self.wizard_model.with_context({"active_ids": self.in_refund.ids})
        )
        self.assertTrue(wizard_form.allow_edit_amount_to_transfer)
        wizard_form.destination_partner_id = self.partner_3
        wizard = wizard_form.save()
        wizard.action_create_move()
        self.assertEqual(self.in_refund.amount_residual, 0.0)

    def test_05_account_move_transfer_partner(self):
        wizard_form = Form(
            self.wizard_model.with_context({"active_ids": self.general_move.ids})
        )
        self.assertTrue(wizard_form.allow_edit_amount_to_transfer)
        self.assertTrue(wizard_form.no_invoice_documents)
        wizard_form.destination_partner_id = self.partner_3
        wizard = wizard_form.save()
        with self.assertRaises(ValidationError):
            wizard.action_create_move()

    def test_06_account_move_transfer_partner(self):
        with Form(
            self.AccountMove.with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = self.today
            invoice_form.partner_id = self.partner_2
            invoice_form.journal_id = self.sale_journal
            invoice_form.currency_id = self.currency_2
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
            self.invoice_with_payment_term = invoice_form.save()
        self.invoice_with_payment_term.action_post()
        wizard_form = Form(
            self.wizard_model.with_context(
                {"active_ids": self.invoice_with_payment_term.ids}
            )
        )
        self.assertTrue(wizard_form.allow_edit_amount_to_transfer)
        wizard_form.destination_partner_id = self.partner_3
        self.assertEqual(
            wizard_form.total_amount_due,
            self.invoice_with_payment_term.currency_id.compute(
                self.invoice_with_payment_term.amount_residual,
                self.env.company.currency_id,
            ),
        )
        wizard_form.currency_id = self.currency_2
        self.assertEqual(
            round(wizard_form.total_amount_due, 2),
            round(self.invoice_with_payment_term.amount_residual, 2),
        )

    def test_07_account_move_transfer_partner(self):
        with Form(
            self.AccountMove.with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = self.today
            invoice_form.partner_id = self.partner_2
            invoice_form.journal_id = self.sale_journal
            invoice_form.invoice_payment_term_id = self.payment_term
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
            self.invoice_with_payment_term = invoice_form.save()
        self.invoice_with_payment_term.action_post()
        wizard_form = Form(
            self.wizard_model.with_context(
                {"active_ids": self.invoice_with_payment_term.ids}
            )
        )
        self.assertTrue(wizard_form.allow_edit_amount_to_transfer)
        wizard_form.destination_partner_id = self.partner_3
        wizard = wizard_form.save()
        action = wizard.action_create_move()
        self.assertEqual(self.invoice_with_payment_term.amount_residual, 0.0)
        new_moves = action.get("domain", []) and self.AccountMove.browse(
            action.get("domain", [])[0][2]
        )
        self.assertEqual(len(new_moves.mapped("line_ids")), 4)
