# Copyright 2025 Le Filament (https://le-filament.com)
# @author: Rémi - Le Filament <remi-filament>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from freezegun import freeze_time

from odoo.tests import tagged

from odoo.addons.account_move_name_sequence.tests.test_account_move_name_seq import (
    TestAccountMoveNameSequence,
)


@tagged("post_install", "-at_install")
class TestAccountMoveNameSequenceHashedJournal(TestAccountMoveNameSequence):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.sales_journal.restrict_mode_hash_table = True

    def test_account_move_hashed(self):
        seq = self.sales_journal.sequence_id
        seq.prefix = "TEST-%(range_year)s-"
        with freeze_time("2022-05-31"):
            move = self.env["account.move"].create(
                {
                    "journal_id": self.sales_journal.id,
                    "partner_id": self.env.ref("base.res_partner_3").id,
                    "move_type": "out_invoice",
                    "invoice_line_ids": self.invoice_line,
                }
            )
            move2 = move.copy()
            move.action_post()
            move2.action_post()
        self.assertEqual(move.name, "TEST-2022-0001")
        self.assertEqual(move2.name, "TEST-2022-0002")
        self.assertEqual(move.sequence_prefix, "TEST-2022-")
        self.assertEqual(move2.sequence_prefix, "TEST-2022-")
        self.assertEqual(move.sequence_number, 1)
        self.assertEqual(move2.sequence_number, 2)

    def test_account_move_hashed_suffix(self):
        seq = self.sales_journal.sequence_id
        seq.prefix = "TEST-%(range_year)s-"
        seq.suffix = "-TEST_SUFFIX"
        with freeze_time("2022-05-31"):
            move = self.env["account.move"].create(
                {
                    "journal_id": self.sales_journal.id,
                    "partner_id": self.env.ref("base.res_partner_3").id,
                    "move_type": "out_invoice",
                    "invoice_line_ids": self.invoice_line,
                }
            )
            move2 = move.copy()
            move.action_post()
            move2.action_post()
        self.assertEqual(move.name, "TEST-2022-0001-TEST_SUFFIX")
        self.assertEqual(move2.name, "TEST-2022-0002-TEST_SUFFIX")
        self.assertEqual(move.sequence_prefix, "TEST-2022-")
        self.assertEqual(move2.sequence_prefix, "TEST-2022-")
        self.assertEqual(move.sequence_number, 1)
        self.assertEqual(move2.sequence_number, 2)
