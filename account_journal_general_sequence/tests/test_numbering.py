# Copyright 2022 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from freezegun import freeze_time

from odoo import fields
from odoo.tests import Form, new_test_user, tagged, users
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@freeze_time("2022-05-11", tick=True)
@tagged("post_install", "-at_install")
class RenumberCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_t1 = cls.company_data["company"]
        cls.company_t2 = cls._create_company(name="company_2_test_numbering_data")
        cls.invoicer = new_test_user(
            cls.env,
            "test_invoicer",
            "account.group_account_invoice",
            company_ids=[fields.Command.set((cls.company_t1 + cls.company_t2).ids)],
        )
        cls.manager = new_test_user(
            cls.env,
            "test_manager",
            "account.group_account_manager",
            company_ids=[fields.Command.set((cls.company_t1 + cls.company_t2).ids)],
        )
        cls.today = fields.Date.to_string(fields.Date.today())

    @users("test_invoicer")
    def test_invoice_gets_entry_number(self):
        # Draft invoice without entry number
        invoice = self.init_invoice(
            "out_invoice", invoice_date=self.today, products=self.product_a
        )
        self.assertFalse(invoice.entry_number)
        # Gets one once posted
        invoice.action_post()
        self.assertTrue(invoice.entry_number.startswith("2022/"))
        # Lost number when canceled
        with mute_logger(
            "odoo.addons.account_journal_general_sequence.models.account_move"
        ):
            invoice.button_cancel()
            self.assertFalse(invoice.entry_number)

    @users("test_manager")
    def test_renumber(self):
        # Post invoices in wrong order
        next_year_invoice = self.init_invoice(
            move_type="out_invoice",
            invoice_date="2023-12-31",
            post=True,
            products=self.product_a,
        )
        next_year_invoice.flush_recordset(["entry_number"])
        new_invoice = self.init_invoice(
            move_type="out_invoice",
            invoice_date="2022-05-10",
            post=True,
            products=self.product_a,
        )
        new_invoice.flush_recordset(["entry_number"])
        old_invoice = self.init_invoice(
            move_type="out_invoice",
            invoice_date="2022-04-30",
            post=True,
            products=self.product_a,
        )
        old_invoice.flush_recordset(["entry_number"])
        self.assertLess(new_invoice.entry_number, old_invoice.entry_number)
        # Fix entry number order with wizard; default values are OK
        wiz_f = Form(
            self.env["account.move.renumber.wizard"].with_company(
                self.company_data["company"]
            )
        )
        self.assertEqual(len(wiz_f.available_sequence_ids), 1)
        wiz = wiz_f.save()
        wiz.action_renumber()
        self.assertGreater(new_invoice.entry_number, old_invoice.entry_number)
        # Add opening move
        opening_invoice = self.init_invoice(
            move_type="out_invoice",
            invoice_date="2022-01-01",
            post=True,
            products=self.product_a,
        )
        self.assertGreater(opening_invoice.entry_number, new_invoice.entry_number)
        # Renumber again, starting from zero
        wiz_f = Form(self.env["account.move.renumber.wizard"])
        wiz = wiz_f.save()
        wiz.action_renumber()
        self.assertEqual(opening_invoice.entry_number, "2022/00000001")
        self.assertEqual(old_invoice.entry_number, "2022/00000002")
        self.assertEqual(new_invoice.entry_number, "2022/00000003")
        self.assertEqual(next_year_invoice.entry_number, "2023/00000001")

    @users("test_invoicer")
    def test_install_no_entry_number(self):
        """No entry numbers assigned on module installation."""
        invoice = self.init_invoice(
            "out_invoice", products=self.product_a, invoice_date=self.today
        )
        self.assertFalse(invoice.entry_number)
        # Imitate installation environment
        self.env["ir.module.module"].sudo().search(
            [("name", "=", "account_journal_general_sequence")]
        ).state = "to install"
        # Do some action that would make the move get an entry number
        invoice.with_context(module="account_journal_general_sequence").action_post()
        # Ensure there's no entry number
        self.assertFalse(invoice.entry_number)

    @users("test_invoicer")
    def test_new_company_journal(self):
        # Create a new invoice for each company
        invoice1 = self.init_invoice(
            "out_invoice",
            products=self.product_a,
            invoice_date=self.today,
            post=True,
            company=self.company_t1,
        )
        invoice2 = self.init_invoice(
            "out_invoice",
            products=self.product_a,
            invoice_date=self.today,
            post=True,
            company=self.company_t2,
        )
        # Each company has a different sequence, so the entry number should be the same
        self.assertEqual(invoice1.entry_number, "2022/00000001")
        self.assertEqual(invoice2.entry_number, "2022/00000001")
