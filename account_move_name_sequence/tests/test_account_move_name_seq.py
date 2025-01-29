# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Moisés López <moylop260@vauxoo.com>
# @author: Francisco Luna <fluna@vauxoo.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMoveNameSequence(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env.ref("base.res_partner_3")
        cls.misc_journal = cls.env["account.journal"].create(
            {
                "name": "Test Journal Move name seq",
                "code": "ADLM",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.sales_seq = cls.env["ir.sequence"].create(
            {
                "name": "TB2C",
                "implementation": "no_gap",
                "prefix": "TB2CSEQ/%(range_year)s/",
                "use_date_range": True,
                "number_increment": 1,
                "padding": 4,
                "company_id": cls.company.id,
            }
        )
        cls.sales_journal = cls.env["account.journal"].create(
            {
                "name": "TB2C",
                "code": "TB2C",
                "type": "sale",
                "company_id": cls.company.id,
                "refund_sequence": True,
                "sequence_id": cls.sales_seq.id,
            }
        )
        cls.purchase_journal = cls.env["account.journal"].create(
            {
                "name": "Test Purchase Journal Move name seq",
                "code": "ADLP",
                "type": "purchase",
                "company_id": cls.company.id,
                "refund_sequence": True,
            }
        )
        cls.accounts = cls.env["account.account"].search(
            [("company_ids", "=", cls.company.id)], limit=2
        )
        cls.account1 = cls.accounts[0]
        cls.account2 = cls.accounts[1]
        cls.date = datetime.now()
        cls.purchase_journal2 = cls.purchase_journal.copy()

        cls.journals = (
            cls.misc_journal
            | cls.purchase_journal
            | cls.sales_journal
            | cls.purchase_journal2
        )
        # This patch was added to avoid test failures in the CI pipeline caused by the
        # `account_journal_restrict_mode` module. It prevents a validation error when
        # disabling restrict mode on journals used in the test, allowing moves to be
        # set to draft and deleted.
        with patch("odoo.models.BaseModel._validate_fields"):
            cls.journals.restrict_mode_hash_table = False

        cls.lines = [
            Command.create({"account_id": cls.account1.id, "debit": 10}),
            Command.create({"account_id": cls.account2.id, "credit": 10}),
        ]
        cls.invoice_line = [
            Command.create(
                {
                    "account_id": cls.account1.id,
                    "price_unit": 42.0,
                    "quantity": 12,
                },
            )
        ]

    def test_seq_creation(self):
        self.assertTrue(self.misc_journal.sequence_id)
        seq = self.misc_journal.sequence_id
        self.assertEqual(seq.company_id, self.company)
        self.assertEqual(seq.implementation, "no_gap")
        self.assertEqual(seq.padding, 4)
        self.assertTrue(seq.use_date_range)
        self.assertTrue(self.purchase_journal.sequence_id)
        self.assertTrue(self.purchase_journal.refund_sequence_id)
        seq = self.purchase_journal.refund_sequence_id
        self.assertEqual(seq.company_id, self.company)
        self.assertEqual(seq.implementation, "no_gap")
        self.assertEqual(seq.padding, 4)
        self.assertTrue(seq.use_date_range)

    def test_misc_move_name(self):
        move = self.env["account.move"].create(
            {
                "date": self.date,
                "journal_id": self.misc_journal.id,
                "line_ids": self.lines,
            }
        )
        self.assertEqual(move.name, "/")
        move.action_post()
        seq = self.misc_journal.sequence_id
        move_name = "{}{}".format(seq.prefix, "1".zfill(seq.padding))
        move_name = move_name.replace("%(range_year)s", str(self.date.year))
        self.assertEqual(move.name, move_name)
        self.assertTrue(seq.date_range_ids)
        drange_count = self.env["ir.sequence.date_range"].search_count(
            [
                ("sequence_id", "=", seq.id),
                ("date_from", "=", fields.Date.add(self.date, month=1, day=1)),
            ]
        )
        self.assertEqual(drange_count, 1)
        move.button_draft()
        move.action_post()
        self.assertEqual(move.name, move_name)

    def test_prefix_move_name_use_move_date(self):
        seq = self.misc_journal.sequence_id
        seq.prefix = "TEST-%(year)s-%(month)s-"
        self.env["ir.sequence.date_range"].sudo().create(
            {
                "date_from": "2021-07-01",
                "date_to": "2022-06-30",
                "sequence_id": seq.id,
            }
        )
        with freeze_time("2022-01-01"):
            move = self.env["account.move"].create(
                {
                    "date": "2021-12-31",
                    "journal_id": self.misc_journal.id,
                    "line_ids": self.lines,
                }
            )
            move.action_post()
        self.assertEqual(move.name, "TEST-2021-12-0001")
        with freeze_time("2022-01-01"):
            move = self.env["account.move"].create(
                {
                    "date": "2022-06-30",
                    "journal_id": self.misc_journal.id,
                    "line_ids": self.lines,
                }
            )
            move.action_post()
        self.assertEqual(move.name, "TEST-2022-06-0002")

        with freeze_time("2022-01-01"):
            move = self.env["account.move"].create(
                {
                    "date": "2022-07-01",
                    "journal_id": self.misc_journal.id,
                    "line_ids": self.lines,
                }
            )
            move.action_post()
        self.assertEqual(move.name, "TEST-2022-07-0001")

    def test_prefix_move_name_use_move_date_2(self):
        seq = self.misc_journal.sequence_id
        seq.prefix = "TEST-%(range_month)s-"
        with freeze_time("2022-01-01"):
            move = self.env["account.move"].create(
                {
                    "date": "2022-06-30",
                    "journal_id": self.misc_journal.id,
                    "line_ids": self.lines,
                }
            )
            move.action_post()
        self.assertEqual(move.name, "TEST-06-0001")

    def test_prefix_move_name_use_move_date_3(self):
        seq = self.misc_journal.sequence_id
        seq.prefix = "TEST-%(range_day)s-"
        with freeze_time("2022-01-01"):
            move = self.env["account.move"].create(
                {
                    "date": "2022-01-01",
                    "journal_id": self.misc_journal.id,
                    "line_ids": self.lines,
                }
            )
            move.action_post()
        self.assertEqual(move.name, "TEST-01-0001")

    def test_in_invoice_and_refund(self):
        in_invoice = self.env["account.move"].create(
            {
                "journal_id": self.purchase_journal.id,
                "invoice_date": self.date,
                "partner_id": self.env.ref("base.res_partner_3").id,
                "move_type": "in_invoice",
                "invoice_line_ids": self.invoice_line
                + [
                    Command.create(
                        {
                            "account_id": self.account1.id,
                            "price_unit": 48.0,
                            "quantity": 10,
                        }
                    )
                ],
            }
        )
        self.assertEqual(in_invoice.name, "/")
        in_invoice.action_post()

        in_invoice = in_invoice.copy(
            {
                "invoice_date": self.date,
            }
        )
        in_invoice.action_post()

        move_reversal = self.env["account.move.reversal"].create(
            {
                "move_ids": in_invoice.ids,
                "journal_id": in_invoice.journal_id.id,
                "reason": "no reason",
            }
        )
        reversal = move_reversal.modify_moves()
        draft_invoice = self.env["account.move"].browse(reversal["res_id"])
        self.assertTrue(draft_invoice)
        self.assertEqual(draft_invoice.state, "draft")
        self.assertEqual(draft_invoice.move_type, "in_invoice")

        in_invoice = in_invoice.copy(
            {
                "invoice_date": self.date,
            }
        )
        in_invoice.action_post()

        move_reversal = self.env["account.move.reversal"].create(
            {
                "move_ids": in_invoice.ids,
                "journal_id": in_invoice.journal_id.id,
                "reason": "no reason",
            }
        )
        reversal = move_reversal.refund_moves()
        draft_reversed_move = self.env["account.move"].browse(reversal["res_id"])
        self.assertTrue(draft_reversed_move)
        self.assertEqual(draft_reversed_move.state, "draft")
        self.assertEqual(draft_reversed_move.move_type, "in_refund")

    def test_in_refund(self):
        in_refund_invoice = self.env["account.move"].create(
            {
                "journal_id": self.purchase_journal.id,
                "invoice_date": self.date,
                "partner_id": self.env.ref("base.res_partner_3").id,
                "move_type": "in_refund",
                "invoice_line_ids": self.invoice_line,
            }
        )
        self.assertEqual(in_refund_invoice.name, "/")
        in_refund_invoice.action_post()
        seq = self.purchase_journal.refund_sequence_id
        move_name = "{}{}".format(seq.prefix, "1".zfill(seq.padding))
        move_name = move_name.replace("%(range_year)s", str(self.date.year))
        self.assertEqual(in_refund_invoice.name, move_name)
        in_refund_invoice.button_draft()
        in_refund_invoice.action_post()
        self.assertEqual(in_refund_invoice.name, move_name)

    def test_remove_invoice_error_secuence_no_grap(self):
        invoice = self.env["account.move"].create(
            {
                "date": self.date,
                "journal_id": self.misc_journal.id,
                "line_ids": self.lines,
            }
        )
        self.assertEqual(invoice.name, "/")
        invoice.action_post()
        error_msg = (
            "You can't delete a posted journal item. "
            "Don’t play games with your accounting records; "
            "reset the journal entry to draft before deleting it."
        )
        with self.assertRaisesRegex(UserError, error_msg):
            invoice.unlink()
        invoice.button_draft()
        invoice.button_cancel()
        invoice.unlink()

    def test_remove_invoice_error_secuence_standard(self):
        implementation = {"implementation": "standard"}
        self.purchase_journal.sequence_id.write(implementation)
        self.purchase_journal.refund_sequence_id.write(implementation)
        in_refund_invoice = self.env["account.move"].create(
            {
                "journal_id": self.purchase_journal.id,
                "invoice_date": self.date,
                "partner_id": self.env.ref("base.res_partner_3").id,
                "move_type": "in_refund",
                "invoice_line_ids": self.invoice_line,
            }
        )
        self.assertEqual(in_refund_invoice.name, "/")
        in_refund_invoice.action_post()
        error_msg = (
            "You can't delete a posted journal item. "
            "Don’t play games with your accounting records; "
            "reset the journal entry to draft before deleting it."
        )
        with self.assertRaisesRegex(UserError, error_msg):
            in_refund_invoice.unlink()
        in_refund_invoice.button_draft()
        in_refund_invoice.button_cancel()
        self.assertTrue(in_refund_invoice.unlink())

    def test_journal_check_journal_sequence(self):
        new_journal = self.purchase_journal2
        # same sequence_id and refund_sequence_id
        with self.assertRaises(ValidationError):
            new_journal.write({"refund_sequence_id": new_journal.sequence_id})

        # company_id in sequence_id or refund_sequence_id to False
        new_sequence_id = new_journal.sequence_id.copy({"company_id": False})
        new_refund_sequence_id = new_journal.refund_sequence_id.copy(
            {"company_id": False}
        )
        with self.assertRaises(ValidationError):
            new_journal.write({"sequence_id": new_sequence_id.id})
        with self.assertRaises(ValidationError):
            new_journal.write({"refund_sequence_id": new_refund_sequence_id.id})

    def test_constrains_date_sequence_true(self):
        self.assertTrue(self.env["account.move"]._constrains_date_sequence())

    def test_prefix_move_name_journal_onchange(self):
        product = self.env["product.product"].create({"name": "Product"})
        with Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = fields.Date.today()
            invoice_form.partner_id = self.partner
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = product
            invoice = invoice_form.save()
            self.assertEqual(invoice.name, "/")
        invoice.journal_id = self.sales_journal
        self.assertEqual(invoice.name, "/", "name based on journal instead of sequence")
        invoice.action_post()
        self.assertIn("TB2CSEQ/", invoice.name, "name was not based on sequence")

    def test_is_end_of_seq_chain(self):
        self.env.user.groups_id -= self.env.ref("account.group_account_manager")
        invoice = self.env["account.move"].create(
            {
                "date": self.date,
                "journal_id": self.misc_journal.id,
                "line_ids": self.lines,
            }
        )
        invoice.action_post()
        error_msg = (
            "You cannot delete this entry, as it has already consumed "
            "a sequence number and is not the last one in the chain. "
            "You should probably revert it instead."
        )
        with self.assertRaisesRegex(UserError, error_msg):
            invoice._unlink_forbid_parts_of_chain()
