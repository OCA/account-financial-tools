# Copyright 2017-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo.exceptions import UserError
from odoo.tests import common


class TestComputeSpreadBoard(common.TransactionCase):
    def setUp(self):
        super().setUp()
        type_receivable = self.env.ref("account.data_account_type_receivable")
        type_expenses = self.env.ref("account.data_account_type_expenses")

        journal = self.env["account.journal"].create(
            {"name": "Test", "type": "general", "code": "test"}
        )

        self.receivable_account = self.env["account.account"].create(
            {
                "name": "test_account_receivable",
                "code": "123",
                "user_type_id": type_receivable.id,
                "reconcile": True,
            }
        )

        self.expense_account = self.env["account.account"].create(
            {
                "name": "test account_expenses",
                "code": "765",
                "user_type_id": type_expenses.id,
                "reconcile": True,
            }
        )

        self.spread_account = self.env["account.account"].create(
            {
                "name": "test spread account_expenses",
                "code": "321",
                "user_type_id": type_expenses.id,
                "reconcile": True,
            }
        )

        self.spread = self.env["account.spread"].create(
            {
                "name": "test",
                "debit_account_id": self.spread_account.id,
                "credit_account_id": self.expense_account.id,
                "period_number": 12,
                "period_type": "month",
                "spread_date": "2017-02-01",
                "estimated_amount": 1000.0,
                "journal_id": journal.id,
                "invoice_type": "in_invoice",
            }
        )

        self.spread2 = self.env["account.spread"].create(
            {
                "name": "test2",
                "debit_account_id": self.spread_account.id,
                "credit_account_id": self.expense_account.id,
                "period_number": 12,
                "period_type": "month",
                "spread_date": "2017-02-01",
                "estimated_amount": 1000.0,
                "journal_id": journal.id,
                "invoice_type": "out_invoice",
            }
        )

    def test_01_supplier_invoice(self):
        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 12)

        self.assertEqual(83.33, spread_lines[0].amount)
        self.assertEqual(83.33, spread_lines[1].amount)
        self.assertEqual(83.33, spread_lines[2].amount)
        self.assertEqual(83.33, spread_lines[3].amount)
        self.assertEqual(83.33, spread_lines[4].amount)
        self.assertEqual(83.33, spread_lines[5].amount)
        self.assertEqual(83.33, spread_lines[6].amount)
        self.assertEqual(83.33, spread_lines[7].amount)
        self.assertEqual(83.33, spread_lines[8].amount)
        self.assertEqual(83.33, spread_lines[9].amount)
        self.assertEqual(83.33, spread_lines[10].amount)
        self.assertEqual(83.37, spread_lines[11].amount)

        self.assertEqual(datetime.date(2017, 2, 28), spread_lines[0].date)
        self.assertEqual(datetime.date(2017, 3, 31), spread_lines[1].date)
        self.assertEqual(datetime.date(2017, 4, 30), spread_lines[2].date)
        self.assertEqual(datetime.date(2017, 5, 31), spread_lines[3].date)
        self.assertEqual(datetime.date(2017, 6, 30), spread_lines[4].date)
        self.assertEqual(datetime.date(2017, 7, 31), spread_lines[5].date)
        self.assertEqual(datetime.date(2017, 8, 31), spread_lines[6].date)
        self.assertEqual(datetime.date(2017, 9, 30), spread_lines[7].date)
        self.assertEqual(datetime.date(2017, 10, 31), spread_lines[8].date)
        self.assertEqual(datetime.date(2017, 11, 30), spread_lines[9].date)
        self.assertEqual(datetime.date(2017, 12, 31), spread_lines[10].date)
        self.assertEqual(datetime.date(2018, 1, 31), spread_lines[11].date)

        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        self.spread.action_recalculate_spread()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertTrue(line.move_id)

    def test_02_supplier_invoice(self):
        # spread date set
        self.spread.write(
            {
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 7),
            }
        )
        self.spread_account.reconcile = True
        self.assertTrue(self.spread_account.reconcile)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 13)

        self.assertEqual(67.20, spread_lines[0].amount)
        self.assertEqual(83.33, spread_lines[1].amount)
        self.assertEqual(83.33, spread_lines[2].amount)
        self.assertEqual(83.33, spread_lines[3].amount)
        self.assertEqual(83.33, spread_lines[4].amount)
        self.assertEqual(83.33, spread_lines[5].amount)
        self.assertEqual(83.33, spread_lines[6].amount)
        self.assertEqual(83.33, spread_lines[7].amount)
        self.assertEqual(83.33, spread_lines[8].amount)
        self.assertEqual(83.33, spread_lines[9].amount)
        self.assertEqual(83.33, spread_lines[10].amount)
        self.assertEqual(83.33, spread_lines[11].amount)
        self.assertEqual(16.17, spread_lines[12].amount)

        self.assertEqual(datetime.date(2017, 1, 31), spread_lines[0].date)
        self.assertEqual(datetime.date(2017, 2, 28), spread_lines[1].date)
        self.assertEqual(datetime.date(2017, 3, 31), spread_lines[2].date)
        self.assertEqual(datetime.date(2017, 4, 30), spread_lines[3].date)
        self.assertEqual(datetime.date(2017, 5, 31), spread_lines[4].date)
        self.assertEqual(datetime.date(2017, 6, 30), spread_lines[5].date)
        self.assertEqual(datetime.date(2017, 7, 31), spread_lines[6].date)
        self.assertEqual(datetime.date(2017, 8, 31), spread_lines[7].date)
        self.assertEqual(datetime.date(2017, 9, 30), spread_lines[8].date)
        self.assertEqual(datetime.date(2017, 10, 31), spread_lines[9].date)
        self.assertEqual(datetime.date(2017, 11, 30), spread_lines[10].date)
        self.assertEqual(datetime.date(2017, 12, 31), spread_lines[11].date)
        self.assertEqual(datetime.date(2018, 1, 31), spread_lines[12].date)

        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

        self.spread.line_ids.create_and_reconcile_moves()
        for line in self.spread.line_ids:
            self.assertTrue(line.move_id)

    def test_03_supplier_invoice(self):
        # spread date set
        self.spread.write(
            {
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 31),
                "move_line_auto_post": False,
            }
        )

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 13)
        self.assertEqual(2.69, spread_lines[0].amount)
        self.assertEqual(83.33, spread_lines[1].amount)
        self.assertEqual(83.33, spread_lines[2].amount)
        self.assertEqual(83.33, spread_lines[3].amount)
        self.assertEqual(83.33, spread_lines[4].amount)
        self.assertEqual(83.33, spread_lines[5].amount)
        self.assertEqual(83.33, spread_lines[6].amount)
        self.assertEqual(83.33, spread_lines[7].amount)
        self.assertEqual(83.33, spread_lines[8].amount)
        self.assertEqual(83.33, spread_lines[9].amount)
        self.assertEqual(83.33, spread_lines[10].amount)
        self.assertEqual(83.33, spread_lines[11].amount)
        self.assertEqual(80.68, spread_lines[12].amount)

        self.assertEqual(datetime.date(2017, 1, 31), spread_lines[0].date)
        self.assertEqual(datetime.date(2017, 2, 28), spread_lines[1].date)
        self.assertEqual(datetime.date(2017, 3, 31), spread_lines[2].date)
        self.assertEqual(datetime.date(2017, 4, 30), spread_lines[3].date)
        self.assertEqual(datetime.date(2017, 5, 31), spread_lines[4].date)
        self.assertEqual(datetime.date(2017, 6, 30), spread_lines[5].date)
        self.assertEqual(datetime.date(2017, 7, 31), spread_lines[6].date)
        self.assertEqual(datetime.date(2017, 8, 31), spread_lines[7].date)
        self.assertEqual(datetime.date(2017, 9, 30), spread_lines[8].date)
        self.assertEqual(datetime.date(2017, 10, 31), spread_lines[9].date)
        self.assertEqual(datetime.date(2017, 11, 30), spread_lines[10].date)
        self.assertEqual(datetime.date(2017, 12, 31), spread_lines[11].date)
        self.assertEqual(datetime.date(2018, 1, 31), spread_lines[12].date)

        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

        spread_lines[0].create_move()
        spread_lines[1].create_move()
        spread_lines[2].create_move()
        self.assertTrue(any(line.move_id for line in spread_lines))
        self.assertTrue(any(not line.move_id for line in spread_lines))

        self.spread._compute_amounts()
        self.assertEqual(self.spread.unspread_amount, 830.65)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 13)
        self.assertEqual(2.69, spread_lines[0].amount)
        self.assertEqual(83.33, spread_lines[1].amount)
        self.assertEqual(83.33, spread_lines[2].amount)
        self.assertEqual(83.33, spread_lines[3].amount)
        self.assertEqual(83.33, spread_lines[4].amount)
        self.assertEqual(83.33, spread_lines[5].amount)
        self.assertEqual(83.33, spread_lines[6].amount)
        self.assertEqual(83.33, spread_lines[7].amount)
        self.assertEqual(83.33, spread_lines[8].amount)
        self.assertEqual(83.33, spread_lines[9].amount)
        self.assertEqual(83.33, spread_lines[10].amount)
        self.assertEqual(83.33, spread_lines[11].amount)
        self.assertEqual(80.68, spread_lines[12].amount)

        self.assertEqual(datetime.date(2017, 1, 31), spread_lines[0].date)
        self.assertEqual(datetime.date(2017, 2, 28), spread_lines[1].date)
        self.assertEqual(datetime.date(2017, 3, 31), spread_lines[2].date)
        self.assertEqual(datetime.date(2017, 4, 30), spread_lines[3].date)
        self.assertEqual(datetime.date(2017, 5, 31), spread_lines[4].date)
        self.assertEqual(datetime.date(2017, 6, 30), spread_lines[5].date)
        self.assertEqual(datetime.date(2017, 7, 31), spread_lines[6].date)
        self.assertEqual(datetime.date(2017, 8, 31), spread_lines[7].date)
        self.assertEqual(datetime.date(2017, 9, 30), spread_lines[8].date)
        self.assertEqual(datetime.date(2017, 10, 31), spread_lines[9].date)
        self.assertEqual(datetime.date(2017, 11, 30), spread_lines[10].date)
        self.assertEqual(datetime.date(2017, 12, 31), spread_lines[11].date)
        self.assertEqual(datetime.date(2018, 1, 31), spread_lines[12].date)

    def test_04_supplier_invoice(self):
        self.spread.write(
            {
                "credit_account_id": self.expense_account.id,
                "debit_account_id": self.spread_account.id,
                "period_number": 3,
                "period_type": "year",
                "spread_date": datetime.date(2018, 10, 24),
            }
        )

        # change the state of invoice to open by clicking Validate button
        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 4)
        self.assertEqual(333.33, spread_lines[1].amount)
        self.assertEqual(333.33, spread_lines[2].amount)
        first_amount = spread_lines[0].amount
        last_amount = spread_lines[3].amount
        remaining_amount = first_amount + last_amount
        self.assertAlmostEqual(remaining_amount, 333.34, places=2)
        total_line_amount = 0.0
        for line in spread_lines:
            total_line_amount += line.amount
        self.assertAlmostEqual(total_line_amount, 1000.0, places=2)

        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_05_supplier_invoice(self):
        # spread date set
        self.spread.write(
            {
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 2, 1),
            }
        )

        self.spread.compute_spread_board()

        # create moves for all the spread lines and open them
        self.spread.line_ids.create_and_reconcile_moves()
        for spread_line in self.spread.line_ids:
            attrs = spread_line.open_move()
            self.assertTrue(isinstance(attrs, dict))

        # unlink all created moves
        self.spread.line_ids.unlink_move()
        for spread_line in self.spread.line_ids:
            self.assertFalse(spread_line.move_id)

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_06_supplier_invoice(self):
        # spread date set
        self.spread.write(
            {"period_number": 3, "period_type": "quarter", "move_line_auto_post": False}
        )

        self.spread.compute_spread_board()

        # create moves for all the spread lines and open them
        self.spread.line_ids.create_and_reconcile_moves()

        # check move lines
        for spread_line in self.spread.line_ids:
            for move_line in spread_line.move_id.line_ids:
                spread_account = self.spread.debit_account_id
                if move_line.account_id == spread_account:
                    debit = move_line.debit
                    self.assertAlmostEqual(debit, spread_line.amount)

        for line in self.spread.line_ids:
            self.assertTrue(line.move_id)
            self.assertFalse(line.move_id.state == "posted")

        self.assertEqual(self.spread.unspread_amount, 0.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

        # try to create move lines again: an error is raised
        for line in self.spread.line_ids:
            with self.assertRaises(UserError):
                line.create_move()

        self.spread.write({"move_line_auto_post": True})
        self.spread.action_recalculate_spread()

        for line in self.spread.line_ids:
            self.assertTrue(line.move_id)
            self.assertTrue(line.move_id.state == "posted")

        self.assertEqual(self.spread.unspread_amount, 0.0)
        self.assertEqual(self.spread.unposted_amount, 0.0)

    def test_07_supplier_invoice(self):
        self.spread.write(
            {
                "period_number": 3,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 1),
                "estimated_amount": 345.96,
            }
        )

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 3)
        self.assertAlmostEquals(115.32, spread_lines[0].amount)
        self.assertAlmostEquals(115.32, spread_lines[1].amount)
        self.assertAlmostEquals(115.32, spread_lines[2].amount)
        self.assertEqual(datetime.date(2017, 1, 31), spread_lines[0].date)
        self.assertEqual(datetime.date(2017, 2, 28), spread_lines[1].date)
        self.assertEqual(datetime.date(2017, 3, 31), spread_lines[2].date)

        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.assertEqual(self.spread.unspread_amount, 345.96)
        self.assertEqual(self.spread.unposted_amount, 345.96)

    def test_08_supplier_invoice(self):
        # spread date set
        self.spread.write(
            {
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 2, 1),
            }
        )

        self.spread.compute_spread_board()
        self.assertTrue(self.spread.line_ids)
        self.spread.action_undo_spread()
        self.assertFalse(self.spread.line_ids)

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_09_supplier_invoice(self):
        # spread date set
        self.spread.write(
            {
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 2, 1),
            }
        )

        self.spread.compute_spread_board()
        for line in self.spread.line_ids:
            line.create_move()
            self.assertTrue(line.move_id)
            action = line.open_move()
            self.assertTrue(action)

        self.spread.line_ids.unlink_move()
        for line in self.spread.line_ids:
            self.assertFalse(line.move_id)
        self.assertTrue(self.spread.line_ids)

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_10_create_entries(self):
        self.env["account.spread.line"]._create_entries()
        self.assertFalse(self.spread.line_ids)

        self.spread.compute_spread_board()
        self.env["account.spread.line"]._create_entries()
        self.assertTrue(self.spread.line_ids)
        for line in self.spread.line_ids:
            self.assertTrue(line.move_id)

    def test_11_create_move_sale_invoice(self):
        self.spread2.move_line_auto_post = False
        self.spread2.compute_spread_board()
        for line in self.spread2.line_ids:
            self.assertFalse(line.move_id)
            line.create_move()
            self.assertTrue(line.move_id)
            self.assertFalse(line.move_id.state == "posted")

        self.spread2.action_undo_spread()
        for line in self.spread2.line_ids:
            self.assertFalse(line.move_id)

        self.spread2.action_recalculate_spread()
        for line in self.spread2.line_ids:
            self.assertTrue(line.move_id)
            self.assertTrue(line.move_id)
            self.assertFalse(line.move_id.state == "posted")
            # try to create move lines again: an error is raised
            with self.assertRaises(UserError):
                line.create_move()

    def test_12_supplier_invoice_auto_post(self):
        # spread date set
        self.spread.write(
            {"period_number": 8, "period_type": "month", "move_line_auto_post": True}
        )

        self.spread.compute_spread_board()

        # create moves for all the spread lines and open them
        self.spread.line_ids.create_and_reconcile_moves()

        # check move lines
        for spread_line in self.spread.line_ids:
            for move_line in spread_line.move_id.line_ids:
                spread_account = self.spread.debit_account_id
                if move_line.account_id == spread_account:
                    debit = move_line.debit
                    self.assertAlmostEqual(debit, spread_line.amount)

        self.assertTrue(self.spread.move_line_auto_post)
        for line in self.spread.line_ids:
            self.assertTrue(line.move_id)
            self.assertTrue(line.move_id.state == "posted")

        self.assertEqual(self.spread.unspread_amount, 0.0)
        self.assertEqual(self.spread.unposted_amount, 0.0)

    def test_13_create_move_in_invoice_auto_post(self):
        self.spread2.write({"period_number": 4, "move_line_auto_post": True})
        self.spread_account.reconcile = True
        self.assertTrue(self.spread_account.reconcile)

        self.spread2.compute_spread_board()
        for line in self.spread2.line_ids:
            self.assertFalse(line.move_id)
            line.create_move()
            self.assertTrue(line.move_id)
            self.assertTrue(line.move_id.state == "posted")

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_14_negative_amount(self):
        # spread date set
        self.spread.write(
            {
                "estimated_amount": -1000.0,
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 7),
            }
        )
        self.spread.compute_spread_board()

        spread_lines = self.spread.line_ids
        self.assertTrue(spread_lines)

    def test_15_compute_spread_board_line_account_deprecated(self):
        self.spread.debit_account_id.deprecated = True
        self.assertTrue(self.spread.debit_account_id.deprecated)

        self.assertTrue(self.spread.is_debit_account_deprecated)
        self.spread.compute_spread_board()

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_16_compute_spread_board_line_account_deprecated(self):
        self.spread.credit_account_id.deprecated = True
        self.assertTrue(self.spread.credit_account_id.deprecated)

        self.assertTrue(self.spread.is_credit_account_deprecated)
        self.spread.compute_spread_board()

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_17_compute_spread_board_line_account_deprecated(self):
        self.spread.compute_spread_board()
        self.spread.debit_account_id.deprecated = True
        self.assertTrue(self.spread.debit_account_id.deprecated)

        for line in self.spread.line_ids:
            self.assertFalse(line.move_id)
            with self.assertRaises(UserError):
                line.create_move()

        self.assertEqual(self.spread.unspread_amount, 1000.0)
        self.assertEqual(self.spread.unposted_amount, 1000.0)

    def test_18_supplier_invoice(self):
        # spread date set
        self.spread.write(
            {
                "period_number": 12,
                "period_type": "month",
                "spread_date": datetime.date(2017, 1, 7),
            }
        )
        self.spread_account.reconcile = True
        self.assertTrue(self.spread_account.reconcile)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 13)

        for line in spread_lines:
            self.assertFalse(line.move_id)

        spread_lines[0]._create_moves().post()
        spread_lines[1]._create_moves().post()
        spread_lines[2]._create_moves().post()
        spread_lines[3]._create_moves().post()

        self.assertEqual(spread_lines[0].move_id.state, "posted")
        self.assertEqual(spread_lines[1].move_id.state, "posted")
        self.assertEqual(spread_lines[2].move_id.state, "posted")
        self.assertEqual(spread_lines[3].move_id.state, "posted")

        self.assertAlmostEqual(self.spread.unspread_amount, 682.81)
        self.assertAlmostEqual(self.spread.unposted_amount, 682.81)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 13)

        self.assertEqual(67.20, spread_lines[0].amount)
        self.assertEqual(83.33, spread_lines[1].amount)
        self.assertEqual(83.33, spread_lines[2].amount)
        self.assertEqual(83.33, spread_lines[3].amount)
        self.assertEqual(83.33, spread_lines[4].amount)
        self.assertEqual(83.33, spread_lines[5].amount)
        self.assertEqual(83.33, spread_lines[6].amount)
        self.assertEqual(83.33, spread_lines[7].amount)
        self.assertEqual(83.33, spread_lines[8].amount)
        self.assertEqual(83.33, spread_lines[9].amount)
        self.assertEqual(83.33, spread_lines[10].amount)
        self.assertEqual(83.33, spread_lines[11].amount)
        self.assertEqual(16.17, spread_lines[12].amount)

        self.assertEqual(datetime.date(2017, 1, 31), spread_lines[0].date)
        self.assertEqual(datetime.date(2017, 2, 28), spread_lines[1].date)
        self.assertEqual(datetime.date(2017, 3, 31), spread_lines[2].date)
        self.assertEqual(datetime.date(2017, 4, 30), spread_lines[3].date)
        self.assertEqual(datetime.date(2017, 5, 31), spread_lines[4].date)
        self.assertEqual(datetime.date(2017, 6, 30), spread_lines[5].date)
        self.assertEqual(datetime.date(2017, 7, 31), spread_lines[6].date)
        self.assertEqual(datetime.date(2017, 8, 31), spread_lines[7].date)
        self.assertEqual(datetime.date(2017, 9, 30), spread_lines[8].date)
        self.assertEqual(datetime.date(2017, 10, 31), spread_lines[9].date)
        self.assertEqual(datetime.date(2017, 11, 30), spread_lines[10].date)
        self.assertEqual(datetime.date(2017, 12, 31), spread_lines[11].date)
        self.assertEqual(datetime.date(2018, 1, 31), spread_lines[12].date)

        self.assertAlmostEqual(self.spread.unspread_amount, 682.81)
        self.assertAlmostEqual(self.spread.unposted_amount, 682.81)
