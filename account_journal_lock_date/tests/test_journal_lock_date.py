# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.account.tests import common


@tagged("post_install", "-at_install")
class TestJournalLockDate(common.AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_move_obj = cls.env["account.move"]
        cls.account_move_line_obj = cls.env["account.move.line"]
        cls.account = cls.company_data["default_account_revenue"]
        cls.account2 = cls.company_data["default_account_expense"]
        cls.journal = cls.company_data["default_journal_bank"]

        # create a move and post it
        cls.move = cls.account_move_obj.create(
            {
                "date": date.today(),
                "journal_id": cls.journal.id,
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
        cls.move.action_post()
        # lock journal, set 'Lock Date for Non-Advisers'
        cls.journal.period_lock_date = date.today() + timedelta(days=2)

    def test_journal_lock_date(self):
        self.env.user.write({"groups_id": [(3, self.ref("base.group_system"))]})
        self.env.user.write(
            {"groups_id": [(3, self.ref("account.group_account_manager"))]}
        )
        self.assertFalse(self.env.user.has_group("account.group_account_manager"))

        # Test that the move cannot be written, or cancelled
        with self.assertRaisesRegex(
            UserError, ".*prior to and inclusive of the lock date.*"
        ):
            self.move.write({"name": "TEST"})

        with self.assertRaisesRegex(
            UserError, ".*prior to and inclusive of the lock date.*"
        ):
            self.move.button_cancel()

        # create a move after the 'Lock Date for Non-Advisers' and post it
        move2 = self.account_move_obj.create(
            {
                "date": self.journal.period_lock_date + timedelta(days=3),
                "journal_id": self.journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.account.id,
                            "credit": 1000.0,
                            "name": "Credit line",
                        },
                    ),
                    Command.create(
                        {
                            "account_id": self.account2.id,
                            "debit": 1000.0,
                            "name": "Debit line",
                        },
                    ),
                ],
            }
        )
        move2.action_post()

        # force create move in a lock date
        move3 = self.account_move_obj.with_context(
            bypass_journal_lock_date=True
        ).create(
            {
                "date": self.journal.period_lock_date,
                "journal_id": self.journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.account.id,
                            "credit": 1000.0,
                            "name": "Credit line",
                        },
                    ),
                    Command.create(
                        {
                            "account_id": self.account2.id,
                            "debit": 1000.0,
                            "name": "Debit line",
                        },
                    ),
                ],
            }
        )
        move3.action_post()

    def test_journal_lock_date_adviser(self):
        """The journal lock date is ignored for Advisers"""
        self.env.user.write(
            {"groups_id": [(4, self.env.ref("account.group_account_manager").id)]}
        )
        self.assertTrue(self.env.user.has_group("account.group_account_manager"))
        wizard = (
            self.env["update.journal.lock.dates.wizard"]
            .with_context(active_model="account.journal", active_ids=self.journal.id)
            .create(
                {
                    "fiscalyear_lock_date": date.today() + timedelta(days=2),
                    "period_lock_date": date.today() + timedelta(days=4),
                }
            )
        )
        wizard.action_update_lock_dates()
        # Advisers cannot write, or cancel moves before 'Lock Date'
        with self.assertRaisesRegex(
            UserError, ".*prior to and inclusive of the lock date.*"
        ):
            self.move.write({"name": "TEST"})

        with self.assertRaisesRegex(
            UserError, ".*prior to and inclusive of the lock date.*"
        ):
            self.move.button_cancel()
        # Advisers can create movements on a date after the 'Lock Date'
        # even if that date is before and inclusive of
        # the 'Lock Date for Non-Advisers' (self.journal.period_lock_date)
        move2 = self.account_move_obj.create(
            {
                "date": self.journal.period_lock_date,
                "journal_id": self.journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.account.id,
                            "credit": 1000.0,
                            "name": "Credit line",
                        },
                    ),
                    Command.create(
                        {
                            "account_id": self.account2.id,
                            "debit": 1000.0,
                            "name": "Debit line",
                        },
                    ),
                ],
            }
        )
        move2.action_post()
