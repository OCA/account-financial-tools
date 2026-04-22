# Copyright 2019 ForgeFlow S.L.
# Copyright 2023 Simone Rubino - Aion Tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import new_test_user
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from odoo.addons.base.tests.common import BaseCommon


class TestAccountLockToDateUpdate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.demo_user = new_test_user(cls.env, login="demo", groups="base.group_user")
        cls.invoicing_group = cls.env.ref("account.group_account_user")
        cls.adviser_group = cls.env.ref("account.group_account_manager")
        cls.UpdateLockToDateUpdateObj = cls.env[
            "account.update.lock_to_date"
        ].with_user(cls.demo_user)
        cls.AccountObj = cls.env["account.account"]
        cls.AccountJournalObj = cls.env["account.journal"]
        cls.AccountMoveObj = cls.env["account.move"]
        cls.demo_user.write({"group_ids": [(4, cls.invoicing_group.id)]})
        cls.bank_journal = cls.AccountJournalObj.create(
            {
                "name": "Bank Journal - BJ",
                "code": "BJ",
                "type": "bank",
                "company_id": cls.company.id,
            }
        )
        cls.sale_journal = cls.AccountJournalObj.create(
            {
                "name": "Sale Journal - SJ",
                "code": "SJ",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )
        cls.purchase_journal = cls.AccountJournalObj.create(
            {
                "name": "Purchase Journal - PJ",
                "code": "PJ",
                "type": "purchase",
                "company_id": cls.company.id,
            }
        )
        cls.account_type_recv = "asset_receivable"
        cls.account_type_rev = "income"

        cls.account_recv = cls.AccountObj.create(
            {
                "code": "RECVDR",
                "name": "Receivable (test)",
                "reconcile": True,
                "account_type": cls.account_type_recv,
            }
        )
        cls.account_sale = cls.AccountObj.create(
            {
                "code": "SALEDR",
                "name": "Receivable (sale)",
                "reconcile": True,
                "account_type": cls.account_type_rev,
            }
        )

    def create_account_move(self, date_str, journal):
        return self.AccountMoveObj.create(
            {
                "journal_id": journal.id,
                "date": date_str,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Debit",
                            "debit": 1000,
                            "account_id": self.account_recv.id,
                        },
                    ),
                    Command.create(
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
                "sale_lock_to_date": "2900-01-01",
                "purchase_lock_to_date": "2900-01-01",
                "fiscalyear_lock_to_date": "2900-01-01",
                "hard_lock_to_date": "2900-01-01",
            }
        )
        self.demo_user.write({"group_ids": [(3, self.adviser_group.id)]})
        with self.assertRaises(ValidationError):
            wizard.with_user(self.demo_user.id).execute()

    def test_02_update_with_access(self):
        wizard = self.create_account_lock_date_update()
        wizard.write(
            {
                "sale_lock_to_date": "2900-01-01",
                "purchase_lock_to_date": "2900-01-01",
                "fiscalyear_lock_to_date": "2900-02-01",
                "hard_lock_to_date": "2900-02-01",
            }
        )
        self.demo_user.write({"group_ids": [(4, self.adviser_group.id)]})
        wizard.with_user(self.demo_user.id).execute()
        self.assertEqual(
            self.company.sale_lock_to_date,
            datetime.strptime("2900-01-01", DEFAULT_SERVER_DATE_FORMAT).date(),
        )
        self.assertEqual(
            self.company.purchase_lock_to_date,
            datetime.strptime("2900-01-01", DEFAULT_SERVER_DATE_FORMAT).date(),
        )
        self.assertEqual(
            self.company.fiscalyear_lock_to_date,
            datetime.strptime("2900-02-01", DEFAULT_SERVER_DATE_FORMAT).date(),
        )
        self.assertEqual(
            self.company.hard_lock_to_date,
            datetime.strptime("2900-02-01", DEFAULT_SERVER_DATE_FORMAT).date(),
        )

    def test_03_create_purchase_move_outside_period(self):
        """We test that we cannot create journal entries after the
        locked date"""
        self.company.purchase_lock_to_date = "2900-01-01"
        self.company.fiscalyear_lock_to_date = "2900-02-01"
        move = self.create_account_move("2900-01-01", self.purchase_journal)
        with self.assertRaises(ValidationError):
            move.with_user(self.demo_user.id).action_post()

    def test_04_create_sale_move_outside_period(self):
        """We test that we cannot create journal entries after the
        locked date"""
        self.company.sale_lock_to_date = "2900-01-01"
        self.company.fiscalyear_lock_to_date = "2900-02-01"
        move = self.create_account_move("2900-01-01", self.sale_journal)
        with self.assertRaises(ValidationError):
            move.with_user(self.demo_user.id).action_post()

    def test_05_create_move_inside_period(self):
        """We test that we can successfully create a journal entry
        within period that is not locked"""
        self.company.sale_lock_to_date = "2900-01-01"
        self.company.purchase_lock_to_date = "2900-01-01"
        self.company.fiscalyear_lock_to_date = "2900-02-01"
        self.company.hard_lock_to_date = "2900-02-01"
        move = self.create_account_move("2800-01-01", self.bank_journal)
        move.with_user(self.demo_user.id).action_post()
        self.assertEqual(move.state, "posted")

    def test_06_lock_period_with_draft_moves(self):
        """We test that we cannot change the hard lock to date
        if there are draft journal entries after that date."""
        self.create_account_move("2900-02-01", self.bank_journal)
        with self.assertRaises(ValidationError):
            self.company.sale_lock_to_date = "2900-01-01"
            self.company.purchase_lock_to_date = "2900-01-01"
            self.company.fiscalyear_lock_to_date = "2900-02-01"
            self.company.hard_lock_to_date = "2900-02-01"
