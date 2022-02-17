# Copyright 2015-2019 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2021 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestAccountInvoiceConstraintChronology(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("base.main_company")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.today = fields.Date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)

        cls.AccountJournal = cls.env["account.journal"]
        cls.sale_journal = cls.AccountJournal.create(
            {
                "name": "Sale journal",
                "code": "SALE",
                "type": "sale",
                "check_chronology": True,
            }
        )

        cls.ProductProduct = cls.env["product.product"]
        cls.product = cls.ProductProduct.create({"name": "Product"})

        cls.AccountMove = cls.env["account.move"]
        with common.Form(
            cls.AccountMove.with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = cls.today
            invoice_form.partner_id = cls.partner_2
            invoice_form.journal_id = cls.sale_journal
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = cls.product
            cls.invoice_1 = invoice_form.save()
        cls.invoice_2 = cls.invoice_1.copy()

        cls.AccountMoveReversal = cls.env["account.move.reversal"]

    def test_journal_type_change(self):
        self.assertTrue(self.sale_journal.check_chronology)

        with common.Form(self.sale_journal) as form:
            form.type = "general"
        self.assertFalse(self.sale_journal.check_chronology)

        with common.Form(self.sale_journal) as form:
            form.type = "sale"
        self.assertFalse(self.sale_journal.check_chronology)

        with common.Form(self.sale_journal) as form:
            form.check_chronology = True
        self.assertTrue(self.sale_journal.check_chronology)

    def test_invoice_draft(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_2.invoice_date = self.today
        with self.assertRaises(UserError):
            self.invoice_2.action_post()

    def test_invoice_draft_nocheck(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_2.invoice_date = self.today
        self.sale_journal.check_chronology = False
        self.invoice_2.action_post()

    def test_invoice_validate(self):
        self.invoice_1.invoice_date = self.tomorrow
        self.invoice_1.action_post()
        self.invoice_2.invoice_date = self.today
        with self.assertRaises(UserError):
            self.invoice_2.action_post()

    def test_invoice_without_date(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_2.invoice_date = False
        with self.assertRaises(UserError):
            self.invoice_2.action_post()

    def test_invoice_refund_before(self):
        self.invoice_1.invoice_date = self.tomorrow
        self.invoice_1.action_post()
        refund = (
            self.AccountMoveReversal.with_context(
                active_model="account.move",
                active_ids=self.invoice_1.ids,
            )
            .create(
                {"date": self.today, "reason": "no reason", "refund_method": "refund"}
            )
            .reverse_moves()
        )
        refund = self.AccountMove.browse(refund["res_id"])
        refund.action_post()

    def test_invoice_refund_before_same_sequence(self):
        self.sale_journal.refund_sequence = False
        self.invoice_1.invoice_date = self.tomorrow
        self.invoice_1.action_post()
        refund = (
            self.AccountMoveReversal.with_context(
                active_model="account.move",
                active_ids=self.invoice_1.ids,
            )
            .create(
                {"date": self.today, "reason": "no reason", "refund_method": "refund"}
            )
            .reverse_moves()
        )
        refund = self.AccountMove.browse(refund["res_id"])
        with self.assertRaises(UserError):
            refund.action_post()

    def test_invoice_higher_number(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_1.action_post()
        self.invoice_1.button_draft()
        self.invoice_1.invoice_date = False

        self.invoice_2.invoice_date = self.today
        self.invoice_2.action_post()

        self.invoice_1.invoice_date = self.tomorrow
        with self.assertRaisesRegex(UserError, "higher number"):
            self.invoice_1.action_post()

    def test_modify_validated_past_invoice(self):
        """We've got an invoice from yesterday that we need to modify but new ones
        have been posted since. As the invoice already has a name, we should be able
        to validate it"""
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_1.action_post()
        self.invoice_2.invoice_date = self.today
        self.invoice_2.action_post()
        self.invoice_1.button_cancel()
        self.invoice_1.button_draft()
        self.invoice_1.action_post()
        self.invoice_1_5 = self.invoice_1.copy()
        self.invoice_1_5.invoice_date = self.yesterday
        with self.assertRaises(UserError):
            self.invoice_1_5.action_post()
