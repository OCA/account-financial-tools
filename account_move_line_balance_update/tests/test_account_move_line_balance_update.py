# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAccountMoveLineBalanceUpdate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.account = cls._create_account("TBU100", "income")
        cls.other_account = cls._create_account("TBU200", "expense")
        cls.foreign_currency = cls.env["res.currency"].search(
            [("id", "!=", cls.company.currency_id.id), ("active", "=", True)], limit=1
        )
        if not cls.foreign_currency:
            cls.foreign_currency = cls.env.ref("base.USD")
            if cls.foreign_currency == cls.company.currency_id:
                cls.foreign_currency = cls.env.ref("base.EUR")
            cls.foreign_currency.active = True
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.move = cls._create_move(cls.account, cls.account)
        cls.line = cls.move.line_ids.filtered("debit")
        cls.counterpart_line = cls.move.line_ids.filtered("credit")

    @classmethod
    def _create_account(cls, code, account_type):
        return cls.env["account.account"].create(
            {
                "name": code,
                "code": code,
                "account_type": account_type,
                "company_id": cls.company.id,
            }
        )

    @classmethod
    def _prepare_line_vals(
        cls, account, debit=0.0, credit=0.0, currency=None, amount_currency=None
    ):
        vals = {
            "name": "Balance update",
            "account_id": account.id,
            "partner_id": cls.partner.id,
            "debit": debit,
            "credit": credit,
        }
        if currency:
            vals.update(
                {
                    "currency_id": currency.id,
                    "amount_currency": amount_currency,
                }
            )
        return vals

    @classmethod
    def _create_move(cls, debit_account, credit_account, currency=None):
        debit_vals = cls._prepare_line_vals(
            debit_account,
            debit=100.0,
            currency=currency,
            amount_currency=125.0,
        )
        credit_vals = cls._prepare_line_vals(
            credit_account,
            credit=100.0,
            currency=currency,
            amount_currency=-125.0,
        )
        return cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2026-01-01"),
                "journal_id": cls.journal.id,
                "line_ids": [
                    Command.create(debit_vals),
                    Command.create(credit_vals),
                ],
            }
        )

    def test_get_balance_update_counterpart_line(self):
        self.assertEqual(
            self.line._get_balance_update_counterpart_line(), self.counterpart_line
        )
        self.assertEqual(
            self.counterpart_line._get_balance_update_counterpart_line(), self.line
        )

    def test_action_open_balance_update_wizard(self):
        action = self.line.action_open_balance_update_wizard()
        self.assertEqual(action["res_model"], "account.move.line.balance.update.wizard")
        self.assertEqual(action["context"]["default_line_id"], self.line.id)
        self.assertEqual(
            action["context"]["default_counterpart_line_id"], self.counterpart_line.id
        )
        self.assertEqual(action["context"]["default_new_balance"], self.line.balance)
        self.assertEqual(
            action["context"]["default_new_amount_currency"], self.line.amount_currency
        )

    def test_action_open_balance_update_wizard_without_counterpart(self):
        move = self._create_move(self.account, self.other_account)
        line = move.line_ids.filtered("debit")
        with self.assertRaises(UserError):
            line.with_context(
                force_same_counterpart_account=True
            ).action_open_balance_update_wizard()

    def test_action_apply(self):
        wizard = self.env["account.move.line.balance.update.wizard"].create(
            {
                "line_id": self.line.id,
                "counterpart_line_id": self.counterpart_line.id,
                "new_balance": 75.0,
            }
        )
        self.assertEqual(wizard.action_apply(), {"type": "ir.actions.act_window_close"})
        self.assertEqual(
            wizard._prepare_update_vals(self.line, 75.0, self.line.amount_currency),
            {"debit": 75.0, "credit": 0.0},
        )
        self.assertEqual(
            wizard._prepare_update_vals(
                self.counterpart_line,
                -75.0,
                self.counterpart_line.amount_currency,
            ),
            {"debit": 0.0, "credit": 75.0},
        )
        self.assertEqual(self.line.balance, 75.0)
        self.assertEqual(self.line.debit, 75.0)
        self.assertEqual(self.counterpart_line.balance, -75.0)
        self.assertEqual(self.counterpart_line.credit, 75.0)

    def test_action_apply_foreign_currency(self):
        move = self._create_move(
            self.account, self.account, currency=self.foreign_currency
        )
        line = move.line_ids.filtered("debit")
        counterpart_line = move.line_ids.filtered("credit")
        wizard = self.env["account.move.line.balance.update.wizard"].create(
            {
                "line_id": line.id,
                "counterpart_line_id": counterpart_line.id,
                "new_amount_currency": 96.0,
            }
        )
        self.assertTrue(wizard.has_foreign_currency)
        self.assertEqual(wizard.current_amount_currency, 125.0)
        self.assertEqual(wizard.counterpart_current_amount_currency, -125.0)
        self.assertEqual(
            wizard._prepare_update_vals(line, 80.0, 96.0),
            {"amount_currency": 96.0},
        )
        self.assertEqual(
            wizard._prepare_update_vals(counterpart_line, -80.0, -96.0),
            {"amount_currency": -96.0},
        )
        self.assertEqual(wizard.action_apply(), {"type": "ir.actions.act_window_close"})
        self.assertEqual(line.amount_currency, 96.0)
        self.assertEqual(counterpart_line.amount_currency, -96.0)
