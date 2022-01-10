# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class TestAccountLockToDateUpdate(TransactionCase):
    def setUp(self):
        super(TestAccountLockToDateUpdate, self).setUp()
        self.company = self.env.ref("base.main_company")
        self.demo_user = self.env.ref("base.user_demo")
        self.adviser_group = self.env.ref("account.group_account_manager")
        self.UpdateLockToDateUpdateObj = self.env[
            "account.update.lock_to_date"
        ].with_user(self.demo_user)
        self.AccountObj = self.env["account.account"]
        self.AccountJournalObj = self.env["account.journal"]
        self.AccountMoveObj = self.env["account.move"]
        self.bank_journal = self.AccountJournalObj.create(
            {
                "name": "Bank Journal - BJ",
                "code": "BJ",
                "type": "bank",
                "company_id": self.company.id,
            }
        )
        self.account_type_recv = self.env.ref("account.data_account_type_receivable")
        self.account_type_rev = self.env.ref("account.data_account_type_revenue")

        self.account_recv = self.AccountObj.create(
            {
                "code": "RECV_DR",
                "name": "Receivable (test)",
                "reconcile": True,
                "user_type_id": self.account_type_recv.id,
            }
        )
        self.account_sale = self.AccountObj.create(
            {
                "code": "SALE_DR",
                "name": "Receivable (sale)",
                "reconcile": True,
                "user_type_id": self.account_type_rev.id,
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

    def create_account_lock_date_update(self):
        return self.UpdateLockToDateUpdateObj.create({"company_id": self.company.id})

    def test_01_update_without_access(self):
        wizard = self.create_account_lock_date_update()
        wizard.write(
            {
                "period_lock_to_date": "2900-01-01",
                "fiscalyear_lock_to_date": "2900-01-01",
            }
        )
        self.demo_user.write({"groups_id": [(3, self.adviser_group.id)]})
        with self.assertRaises(ValidationError):
            wizard.with_user(self.demo_user.id).execute()

    def test_02_update_with_access(self):
        wizard = self.create_account_lock_date_update()
        wizard.write(
            {
                "period_lock_to_date": "2900-01-01",
                "fiscalyear_lock_to_date": "2900-02-01",
            }
        )
        self.demo_user.write({"groups_id": [(4, self.adviser_group.id)]})
        wizard.with_user(self.demo_user.id).execute()
        self.assertEqual(
            self.company.period_lock_to_date,
            datetime.strptime("2900-01-01", DEFAULT_SERVER_DATE_FORMAT).date(),
        )
        self.assertEqual(
            self.company.fiscalyear_lock_to_date,
            datetime.strptime("2900-02-01", DEFAULT_SERVER_DATE_FORMAT).date(),
        )

    def test_03_create_move_outside_period(self):
        """We test that we cannot create journal entries after the
        locked date"""
        self.company.period_lock_to_date = "2900-01-01"
        self.company.fiscalyear_lock_to_date = "2900-02-01"
        move = self.create_account_move("2900-01-01")
        with self.assertRaises(ValidationError):
            move.with_user(self.demo_user.id).action_post()

    def test_04_create_move_inside_period(self):
        """We test that we can successfully create a journal entry
        within period that is not locked"""
        self.company.period_lock_to_date = "2900-01-01"
        self.company.fiscalyear_lock_to_date = "2900-02-01"
        move = self.create_account_move("2800-01-01")
        move.with_user(self.demo_user.id).action_post()
        self.assertEqual(move.state, "posted")

    def test_05_lock_period_with_draft_moves(self):
        """We test that we cannot change the fiscal year lock to date
        if there are draft journal entries after that date."""
        self.create_account_move("2900-02-01")
        with self.assertRaises(ValidationError):
            self.company.period_lock_to_date = "2900-01-01"
            self.company.fiscalyear_lock_to_date = "2900-02-01"
