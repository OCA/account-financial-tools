# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestAccountCashDeposit(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.currency = self.company.currency_id
        self.cash_journal = self.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", self.company.id)], limit=1
        )
        self.bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", self.company.id)], limit=1
        )
        self.cash_unit_note = self.env["cash.unit"].search(
            [("currency_id", "=", self.currency.id), ("cash_type", "=", "note")],
            limit=1,
        )
        self.cash_unit_coinroll = self.env["cash.unit"].search(
            [("currency_id", "=", self.currency.id), ("cash_type", "=", "coinroll")],
            limit=1,
        )
        self.all_cash_units = self.env["cash.unit"].search(
            [("currency_id", "=", self.currency.id)]
        )
        self.date = date.today()
        self.yesterday = date.today() - timedelta(days=1)
        self.deposit_seq = self.env["ir.sequence"].search(
            [("code", "=", "account.cash.deposit")]
        )
        self.order_seq = self.env["ir.sequence"].search(
            [("code", "=", "account.cash.order")]
        )

    def test_cash_order(self):
        self.all_cash_units.write({"auto_create": "both"})
        order = (
            self.env["account.cash.deposit"]
            .with_context(default_operation_type="order")
            .create(
                {
                    "company_id": self.company.id,
                    "currency_id": self.currency.id,
                    "cash_journal_id": self.cash_journal.id,
                    "bank_journal_id": self.bank_journal.id,
                }
            )
        )
        self.assertEqual(len(order.line_ids), len(self.all_cash_units))
        self.assertEqual(order.state, "draft")
        self.assertTrue(order.name.startswith(self.order_seq.prefix))
        self.assertEqual(order.operation_type, "order")
        line_note = self.env["account.cash.deposit.line"].search(
            [
                ("cash_unit_id", "=", self.cash_unit_note.id),
                ("parent_id", "=", order.id),
            ]
        )
        line_note.write({"qty": 5})
        line_note = self.env["account.cash.deposit.line"].search(
            [
                ("cash_unit_id", "=", self.cash_unit_coinroll.id),
                ("parent_id", "=", order.id),
            ]
        )
        line_note.write({"qty": 2})
        total = (
            5 * self.cash_unit_note.total_value
            + 2 * self.cash_unit_coinroll.total_value
        )
        self.assertFalse(order.currency_id.compare_amounts(order.total_amount, total))
        order.confirm_order()
        self.assertEqual(order.state, "confirmed")
        self.assertEqual(len(order.line_ids), 2)
        wizard = (
            self.env["account.cash.order.reception"]
            .with_context(default_order_id=order.id)
            .create({"date": self.yesterday})
        )
        wizard.run()
        self.assertEqual(order.state, "done")
        self.assertEqual(order.date, self.yesterday)
        self.assertTrue(order.move_id)
        self.assertEqual(len(order.move_id.line_ids), 2)
        self.assertEqual(order.move_id.date, order.date)
        self.assertEqual(order.move_id.journal_id, order.cash_journal_id)
        self.assertEqual(order.move_id.ref, order.display_name)

    def test_cash_deposit(self):
        deposit = (
            self.env["account.cash.deposit"]
            .with_context(default_operation_type="deposit")
            .create(
                {
                    "company_id": self.company.id,
                    "currency_id": self.currency.id,
                    "cash_journal_id": self.cash_journal.id,
                    "bank_journal_id": self.bank_journal.id,
                    "line_ids": [
                        (0, 0, {"cash_unit_id": self.cash_unit_note.id, "qty": 3}),
                        (0, 0, {"cash_unit_id": self.cash_unit_coinroll.id, "qty": 6}),
                    ],
                }
            )
        )
        self.assertEqual(len(deposit.line_ids), 2)
        self.assertEqual(deposit.state, "draft")
        self.assertTrue(deposit.name.startswith(self.deposit_seq.prefix))
        self.assertEqual(deposit.operation_type, "deposit")
        total = (
            3 * self.cash_unit_note.total_value
            + 6 * self.cash_unit_coinroll.total_value
        )
        self.assertFalse(
            deposit.currency_id.compare_amounts(deposit.total_amount, total)
        )
        deposit.validate()
        self.assertEqual(deposit.state, "done")
        self.assertTrue(deposit.move_id)
        self.assertEqual(len(deposit.move_id.line_ids), 2)
        self.assertEqual(deposit.move_id.date, deposit.date)
        self.assertEqual(deposit.move_id.journal_id, deposit.cash_journal_id)
        self.assertEqual(deposit.move_id.ref, deposit.display_name)
