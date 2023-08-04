# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestAccountMoveFiscalMonth(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountObj = cls.env["account.account"]
        cls.AccountJournalObj = cls.env["account.journal"]
        cls.AccountMoveObj = cls.env["account.move"]
        cls.DateRangeObj = cls.env["date.range"]

        cls.bank_journal = cls.AccountJournalObj.search(
            [("type", "=", "bank")], limit=1
        )

        cls.account_recv = cls.AccountObj.create(
            {
                "code": "RECVDR",
                "name": "Receivable (test)",
                "reconcile": True,
                "account_type": "asset_receivable",
            }
        )
        cls.account_sale = cls.AccountObj.create(
            {
                "code": "SALEDR",
                "name": "Receivable (sale)",
                "reconcile": True,
                "account_type": "income",
            }
        )

        cls.date_range_type_month = cls.env.ref(
            "account_fiscal_month.date_range_fiscal_month"
        )

        cls.date_range_january_2017 = cls.DateRangeObj.create(
            {
                "name": "January 2017",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
                "type_id": cls.date_range_type_month.id,
            }
        )

        cls.date_range_february_2017 = cls.DateRangeObj.create(
            {
                "name": "February 2017",
                "date_start": "2017-02-01",
                "date_end": "2017-02-28",
                "type_id": cls.date_range_type_month.id,
            }
        )

        cls.date_range_january_2018 = cls.DateRangeObj.create(
            {
                "name": "January 2018",
                "date_start": "2018-01-01",
                "date_end": "2018-01-31",
                "type_id": cls.date_range_type_month.id,
            }
        )

    def create_account_move(self, date_str):
        return self.AccountMoveObj.create(
            {
                "journal_id": self.bank_journal.id,
                "date": date_str,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Debit",
                            "debit": 1000,
                            "account_id": self.account_recv.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Credit",
                            "credit": 1000,
                            "account_id": self.account_sale.id,
                        },
                    ),
                ],
            }
        )

    def test_01_account_move_date_range_fm_id_compute(self):
        january_1st = Date.from_string("2017-01-01")
        move = self.create_account_move(january_1st)

        self.assertEqual(
            move.date_range_fm_id,
            self.date_range_january_2017,
            msg="Move period should be January 2017",
        )
        self.assertTrue(
            all(
                [
                    line.date_range_fm_id == self.date_range_january_2017
                    for line in move.line_ids
                ]
            ),
            msg="All lines period should be January 2017",
        )

        march_1st = Date.from_string("2017-03-01")
        move = self.create_account_move(march_1st)
        self.assertFalse(
            bool(move.date_range_fm_id), msg="Move shouldn't have any date range"
        )

    def test_02_account_move_date_range_fm_id_search(self):
        january_2017_1st = Date.from_string("2017-01-01")
        february_2017_1st = Date.from_string("2017-02-01")
        march_2017_1st = Date.from_string("2017-03-01")
        january_2018_1st = Date.from_string("2018-01-01")

        move_jan_2017 = self.create_account_move(january_2017_1st)
        move_feb_2017 = self.create_account_move(february_2017_1st)
        move_march_2017 = self.create_account_move(march_2017_1st)
        move_jan_2018 = self.create_account_move(january_2018_1st)

        moves = self.AccountMoveObj.search([("date_range_fm_id", "ilike", "January")])

        self.assertTrue(
            all(
                [
                    move_jan_2017 in moves,
                    move_feb_2017 not in moves,
                    move_march_2017 not in moves,
                    move_jan_2018 in moves,
                ]
            ),
            msg="There should be only moves in January",
        )

        moves = self.AccountMoveObj.search([("date_range_fm_id", "ilike", "2017")])

        self.assertTrue(
            all(
                [
                    move_jan_2017 in moves,
                    move_feb_2017 in moves,
                    move_march_2017 not in moves,
                    move_jan_2018 not in moves,
                ]
            )
        )

        moves = self.AccountMoveObj.search(
            [("date_range_fm_id", "=", self.date_range_january_2017.id)]
        )

        self.assertTrue(
            all(
                [
                    move_jan_2017 in moves,
                    move_feb_2017 not in moves,
                    move_march_2017 not in moves,
                    move_jan_2018 not in moves,
                ]
            )
        )

        moves = self.AccountMoveObj.search(
            [
                (
                    "date_range_fm_id",
                    "in",
                    (self.date_range_january_2017.id, self.date_range_february_2017.id),
                ),
            ]
        )

        self.assertTrue(
            all(
                [
                    move_jan_2017 in moves,
                    move_feb_2017 in moves,
                    move_march_2017 not in moves,
                    move_jan_2018 not in moves,
                ]
            )
        )
