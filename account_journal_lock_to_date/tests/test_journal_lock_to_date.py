# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests import common


@tagged("post_install", "-at_install")
class TestJournalLockToDate(common.AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_move_obj = cls.env["account.move"]
        cls.account = cls.company_data["default_account_revenue"]
        cls.account2 = cls.company_data["default_account_expense"]
        cls.journal = cls.company_data["default_journal_bank"]
        cls.other_journal = cls.company_data["default_journal_misc"]
        cls.today = date.today()
        # a move posted in the future before any lock to date is set
        cls.move = cls._create_move(cls.today + timedelta(days=5))
        cls.move.action_post()

    @classmethod
    def _create_move(cls, move_date, journal=None):
        return cls.account_move_obj.create(
            {
                "date": move_date,
                "journal_id": (journal or cls.journal).id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": cls.account.id,
                            "credit": 1000.0,
                            "name": "Credit line",
                        },
                    ),
                    Command.create(
                        {
                            "account_id": cls.account2.id,
                            "debit": 1000.0,
                            "name": "Debit line",
                        },
                    ),
                ],
            }
        )

    def _remove_adviser_group(self):
        self.env.user.write({"groups_id": [(3, self.ref("base.group_system"))]})
        self.env.user.write(
            {"groups_id": [(3, self.ref("account.group_account_manager"))]}
        )
        self.assertFalse(self.env.user.has_group("account.group_account_manager"))

    def _update_lock_to_dates(
        self, journals, fiscalyear_lock_to_date, period_lock_to_date
    ):
        wizard = (
            self.env["update.journal.lock.to.dates.wizard"]
            .with_context(active_model="account.journal", active_ids=journals.ids)
            .create(
                {
                    "fiscalyear_lock_to_date": fiscalyear_lock_to_date,
                    "period_lock_to_date": period_lock_to_date,
                }
            )
        )
        wizard.action_update_lock_to_dates()

    def test_journal_lock_to_date_non_adviser(self):
        self.journal.period_lock_to_date = self.today + timedelta(days=2)
        self._remove_adviser_group()

        # A posted move after the lock to date cannot be modified
        with self.assertRaisesRegex(
            UserError, ".*posterior to and inclusive of the lock to date.*"
        ):
            self.move.write({"name": "TEST"})
        with self.assertRaisesRegex(
            UserError, ".*posterior to and inclusive of the lock to date.*"
        ):
            self.move.button_draft()

        # A move on the lock to date cannot be posted
        move2 = self._create_move(self.journal.period_lock_to_date)
        with self.assertRaisesRegex(
            UserError, ".*posterior to and inclusive of the lock to date.*"
        ):
            move2.action_post()

        # A move before the lock to date can be posted
        move3 = self._create_move(self.today + timedelta(days=1))
        move3.action_post()
        self.assertEqual(move3.state, "posted")

        # Other journals are not affected
        move4 = self._create_move(self.today + timedelta(days=10), self.other_journal)
        move4.action_post()
        self.assertEqual(move4.state, "posted")

        # The check can be bypassed
        move5 = self._create_move(self.journal.period_lock_to_date)
        move5.with_context(bypass_journal_lock_to_date=True).action_post()
        self.assertEqual(move5.state, "posted")

    def test_journal_lock_to_date_non_adviser_both_dates(self):
        """Non-Advisers are blocked by the earliest of both dates"""
        self.journal.write(
            {
                "fiscalyear_lock_to_date": self.today + timedelta(days=2),
                "period_lock_to_date": self.today + timedelta(days=4),
            }
        )
        self._remove_adviser_group()
        move2 = self._create_move(self.today + timedelta(days=3))
        with self.assertRaisesRegex(
            UserError, ".*posterior to and inclusive of the lock to date.*"
        ):
            move2.action_post()

    def test_journal_lock_to_date_adviser(self):
        """The 'Lock To Date for Non-Advisers' is ignored for Advisers"""
        self.assertTrue(self.env.user.has_group("account.group_account_manager"))
        self._update_lock_to_dates(
            self.journal,
            self.today + timedelta(days=4),
            self.today + timedelta(days=2),
        )
        self.assertEqual(
            self.journal.fiscalyear_lock_to_date, self.today + timedelta(days=4)
        )
        self.assertEqual(
            self.journal.period_lock_to_date, self.today + timedelta(days=2)
        )

        # Advisers cannot modify moves after the 'Lock To Date'
        with self.assertRaisesRegex(
            UserError, ".*posterior to and inclusive of the lock to date.*"
        ):
            self.move.button_draft()

        # Advisers can post moves before the 'Lock To Date' even if
        # after the 'Lock To Date for Non-Advisers'
        move2 = self._create_move(self.today + timedelta(days=3))
        move2.action_post()
        self.assertEqual(move2.state, "posted")

    def test_update_wizard_non_adviser(self):
        wizard = (
            self.env["update.journal.lock.to.dates.wizard"]
            .with_context(active_model="account.journal", active_ids=self.journal.ids)
            .create({"fiscalyear_lock_to_date": self.today})
        )
        user = new_test_user(
            self.env, login="billing_user", groups="account.group_account_invoice"
        )
        with self.assertRaisesRegex(UserError, "not allowed"):
            wizard.with_user(user).action_update_lock_to_dates()
        self.assertFalse(self.journal.fiscalyear_lock_to_date)
