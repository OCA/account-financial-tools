# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestAccountMoveFiscalYear(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountObj = cls.env["account.account"]
        cls.AccountJournalObj = cls.env["account.journal"]
        cls.AccountMoveObj = cls.env["account.move"]
        cls.DateRangeObj = cls.env["account.fiscal.year"]

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

        cls.date_range_2017 = cls.DateRangeObj.create(
            {
                "name": "2017",
                "date_from": "2017-01-01",
                "date_to": "2017-12-31",
            }
        )

        cls.date_range_2018 = cls.DateRangeObj.create(
            {
                "name": "2018",
                "date_from": "2018-01-01",
                "date_to": "2018-12-31",
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

    def test_01_account_move_date_range_fy_id_compute(self):
        january_1st = Date.to_date("2017-01-01")
        move = self.create_account_move(january_1st)

        self.assertEqual(
            move.date_range_fy_id,
            self.date_range_2017,
            msg="Move period should be 2017",
        )
        self.assertTrue(
            all(
                [
                    line.date_range_fy_id == self.date_range_2017
                    for line in move.line_ids
                ]
            ),
            msg="All lines period should be 2017",
        )

        january_2019 = Date.to_date("2019-01-01")
        move = self.create_account_move(january_2019)
        self.assertFalse(
            bool(move.date_range_fy_id), msg="Move shouldn't have any date range"
        )

    def test_02_account_move_date_range_fy_id_search(self):
        january_2017 = Date.to_date("2017-01-01")
        january_2018 = Date.to_date("2018-01-01")
        january_2019 = Date.to_date("2019-01-01")

        move_2017 = self.create_account_move(january_2017)
        move_2018 = self.create_account_move(january_2018)
        move_2019 = self.create_account_move(january_2019)

        moves = self.AccountMoveObj.search(
            [
                ("date_range_fy_id", "ilike", "2017"),
            ]
        )

        self.assertTrue(
            all(
                [
                    move_2017 in moves,
                    move_2018 not in moves,
                    move_2019 not in moves,
                ]
            ),
            msg="There should be only moves in 2017",
        )

        moves = self.AccountMoveObj.search(
            [
                ("date_range_fy_id", "=", self.date_range_2017.id),
            ]
        )

        self.assertTrue(
            all(
                [
                    move_2017 in moves,
                    move_2018 not in moves,
                    move_2019 not in moves,
                ]
            )
        )

        moves = self.AccountMoveObj.search(
            [
                (
                    "date_range_fy_id",
                    "in",
                    (self.date_range_2017.id, self.date_range_2018.id),
                ),
            ]
        )

        self.assertTrue(
            all(
                [
                    move_2017 in moves,
                    move_2018 in moves,
                    move_2019 not in moves,
                ]
            )
        )
