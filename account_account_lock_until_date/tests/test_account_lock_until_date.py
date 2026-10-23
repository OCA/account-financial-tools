# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.account.models.account_move import BYPASS_LOCK_CHECK
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountLockUntilDate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.company_data["default_account_revenue"]
        cls.account.lock_until_date = "2026-01-31"
        cls.counterpart = cls.company_data["default_account_expense"]

    def _create_move(self, move_date):
        return self.env["account.move"].create(
            {
                "date": move_date,
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create({"account_id": self.account.id, "credit": 100.0}),
                    Command.create({"account_id": self.counterpart.id, "debit": 100.0}),
                ],
            }
        )

    def test_post_on_lock_until_date(self):
        move = self._create_move("2026-01-31")
        with self.assertRaisesRegex(UserError, "is locked until"):
            move.action_post()

    def test_post_after_lock_until_date(self):
        move = self._create_move("2026-02-01")
        move.action_post()
        self.assertEqual(move.state, "posted")

    def test_post_without_lock_until_date(self):
        self.account.lock_until_date = False
        move = self._create_move("2026-01-31")
        move.action_post()
        self.assertEqual(move.state, "posted")

    def test_check_with_bypass(self):
        move = self._create_move("2026-01-31")
        move = move.with_context(bypass_lock_check=BYPASS_LOCK_CHECK)
        move._check_fiscal_lock_dates()
