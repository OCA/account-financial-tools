# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountMoveNameSequence(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.misc_journal = self.env["account.journal"].create(
            {
                "name": "Test Journal Move name seq",
                "code": "ADLM",
                "type": "general",
                "company_id": self.company.id,
            }
        )
        self.purchase_journal = self.env["account.journal"].create(
            {
                "name": "Test Purchase Journal Move name seq",
                "code": "ADLP",
                "type": "purchase",
                "company_id": self.company.id,
                "refund_sequence": True,
            }
        )
        self.accounts = self.env["account.account"].search(
            [("company_id", "=", self.company.id)], limit=2
        )
        self.account1 = self.accounts[0]
        self.account2 = self.accounts[1]
        self.date = datetime.now()

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
                "line_ids": [
                    (0, 0, {"account_id": self.account1.id, "debit": 10}),
                    (0, 0, {"account_id": self.account2.id, "credit": 10}),
                ],
            }
        )
        self.assertEqual(move.name, "/")
        move.action_post()
        seq = self.misc_journal.sequence_id
        move_name = "%s%s" % (seq.prefix, "1".zfill(seq.padding))
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

    def test_in_refund(self):
        in_refund_invoice = self.env["account.move"].create(
            {
                "journal_id": self.purchase_journal.id,
                "invoice_date": self.date,
                "partner_id": self.env.ref("base.res_partner_3").id,
                "move_type": "in_refund",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account1.id,
                            "price_unit": 42.0,
                            "quantity": 12,
                        },
                    )
                ],
            }
        )
        self.assertEqual(in_refund_invoice.name, "/")
        in_refund_invoice.action_post()
        seq = self.purchase_journal.refund_sequence_id
        move_name = "%s%s" % (seq.prefix, "1".zfill(seq.padding))
        move_name = move_name.replace("%(range_year)s", str(self.date.year))
        self.assertEqual(in_refund_invoice.name, move_name)
        in_refund_invoice.button_draft()
        in_refund_invoice.action_post()
        self.assertEqual(in_refund_invoice.name, move_name)
