# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.account.models.account_move import BYPASS_LOCK_CHECK
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountLockToDate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.company_data["default_account_revenue"]
        cls.counterpart = cls.company_data["default_account_expense"]
        # a move posted after the future lock to date, before it is set
        cls.posted_move = cls._create_move("2026-02-15")
        cls.posted_move.action_post()
        cls.account.lock_to_date = "2026-01-31"

    @classmethod
    def _create_move(cls, move_date):
        return cls.env["account.move"].create(
            {
                "date": move_date,
                "journal_id": cls.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create({"account_id": cls.account.id, "credit": 100.0}),
                    Command.create({"account_id": cls.counterpart.id, "debit": 100.0}),
                ],
            }
        )

    def test_post_on_lock_to_date(self):
        move = self._create_move("2026-01-31")
        with self.assertRaisesRegex(UserError, "is locked from"):
            move.action_post()

    def test_post_after_lock_to_date(self):
        move = self._create_move("2026-02-01")
        with self.assertRaisesRegex(UserError, "is locked from"):
            move.action_post()

    def test_post_before_lock_to_date(self):
        move = self._create_move("2026-01-30")
        move.action_post()
        self.assertEqual(move.state, "posted")

    def test_post_without_lock_to_date(self):
        self.account.lock_to_date = False
        move = self._create_move("2026-02-01")
        move.action_post()
        self.assertEqual(move.state, "posted")

    def test_posted_move_after_lock_to_date(self):
        with self.assertRaisesRegex(UserError, "is locked from"):
            self.posted_move.button_draft()

    def test_change_date_into_locked_period(self):
        move = self._create_move("2026-01-15")
        move.action_post()
        # skip the core readonly check on posted moves to reach the lock check
        with self.assertRaisesRegex(UserError, "is locked from"):
            move.with_context(skip_readonly_check=True).date = "2026-01-31"

    def test_check_with_bypass(self):
        move = self._create_move("2026-01-31")
        move = move.with_context(bypass_lock_check=BYPASS_LOCK_CHECK)
        move._check_fiscal_lock_dates()

    def test_update_wizard(self):
        accounts = self.account | self.counterpart
        wizard = (
            self.env["update.account.lock.to.dates.wizard"]
            .with_context(active_model="account.account", active_ids=accounts.ids)
            .create({"lock_to_date": "2026-03-31"})
        )
        wizard.action_update_lock_to_dates()
        self.assertEqual(
            accounts.mapped("lock_to_date"),
            [wizard.lock_to_date, wizard.lock_to_date],
        )

    def test_update_wizard_non_adviser(self):
        wizard = (
            self.env["update.account.lock.to.dates.wizard"]
            .with_context(
                active_model="account.account", active_ids=self.counterpart.ids
            )
            .create({"lock_to_date": "2026-03-31"})
        )
        user = new_test_user(
            self.env, login="billing_user", groups="account.group_account_invoice"
        )
        with self.assertRaisesRegex(UserError, "not allowed"):
            wizard.with_user(user).action_update_lock_to_dates()
        self.assertFalse(self.counterpart.lock_to_date)
