# Copyright 2019 ForgeFlow S.L.
# Copyright 2023 Simone Rubino - Aion Tech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import new_test_user

from odoo.addons.account.models.account_move import BYPASS_LOCK_CHECK
from odoo.addons.base.tests.common import BaseCommon


class TestAccountLockToDateUpdate(BaseCommon):
    # Keep running the tests as the setup user: since 20.0, BaseCommon runs
    # them as a plain internal user by default.
    _test_user_groups = None

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
            fields.Date.to_date("2900-01-01"),
        )
        self.assertEqual(
            self.company.purchase_lock_to_date,
            fields.Date.to_date("2900-01-01"),
        )
        self.assertEqual(
            self.company.fiscalyear_lock_to_date,
            fields.Date.to_date("2900-02-01"),
        )
        self.assertEqual(
            self.company.hard_lock_to_date,
            fields.Date.to_date("2900-02-01"),
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

    def test_07_advance_hard_lock_to_date(self):
        """Test that hard_lock_to_date can be advanced forward into future periods."""
        self.demo_user.write({"group_ids": [(4, self.adviser_group.id)]})
        wizard = self.create_account_lock_date_update()
        wizard.write({"hard_lock_to_date": "2900-01-01"})
        wizard.with_user(self.demo_user.id).execute()
        self.assertEqual(
            self.company.hard_lock_to_date,
            fields.Date.to_date("2900-01-01"),
        )
        wizard2 = self.create_account_lock_date_update()
        wizard2.write({"hard_lock_to_date": "2900-02-01"})
        wizard2.with_user(self.demo_user.id).execute()
        self.assertEqual(
            self.company.hard_lock_to_date,
            fields.Date.to_date("2900-02-01"),
        )
        move = self.create_account_move("2900-01-15", self.bank_journal)
        move.with_user(self.demo_user.id).action_post()
        self.assertEqual(move.state, "posted")

    def _create_lock_to_date_exception(self, user, lock_date):
        return self.env["account.lock_exception"].create(
            {
                "company_id": self.company.id,
                "user_id": user.id,
                "reason": "Test",
                "lock_date_field": "fiscalyear_lock_to_date",
                "lock_date": lock_date,
            }
        )

    def test_08_lock_to_date_exception_for_user(self):
        """An exception lets its user post after the lock to date, not the others."""
        self.company.fiscalyear_lock_to_date = "2900-01-01"
        self._create_lock_to_date_exception(self.demo_user, "2900-03-01")
        self.assertEqual(
            self.company.with_user(self.demo_user).user_fiscalyear_lock_to_date,
            fields.Date.to_date("2900-03-01"),
        )
        self.assertEqual(
            self.company.user_fiscalyear_lock_to_date,
            fields.Date.to_date("2900-01-01"),
        )
        move = self.create_account_move("2900-02-01", self.bank_journal)
        move.with_user(self.demo_user).action_post()
        self.assertEqual(move.state, "posted")
        other_move = self.create_account_move("2900-02-01", self.bank_journal)
        with self.assertRaises(ValidationError):
            other_move.action_post()
        late_move = self.create_account_move("2900-03-15", self.bank_journal)
        with self.assertRaises(ValidationError):
            late_move.with_user(self.demo_user).action_post()

    def test_09_lock_to_date_exception_search_and_recreate(self):
        """Search on the lock to date fields of the exceptions, and recreate
        the active exceptions when the company lock to date changes."""
        self.company.fiscalyear_lock_to_date = "2900-01-01"
        exception = self._create_lock_to_date_exception(self.demo_user, "2900-03-01")
        Exception = self.env["account.lock_exception"]
        self.assertIn(
            exception,
            Exception.search([("fiscalyear_lock_to_date", ">", "2900-02-01")]),
        )
        self.assertNotIn(
            exception, Exception.search([("sale_lock_to_date", ">", "2900-02-01")])
        )
        self.assertNotIn(
            exception,
            Exception.search([("purchase_lock_to_date", ">=", "2900-02-01")]),
        )
        with self.assertRaises(UserError):
            Exception.search([("fiscalyear_lock_to_date", "<", "2900-02-01")])
        self.company.fiscalyear_lock_to_date = "2900-01-15"
        self.assertEqual(exception.state, "revoked")
        new_exception = Exception.search(
            [
                ("company_id", "=", self.company.id),
                ("state", "=", "active"),
                ("lock_date_field", "=", "fiscalyear_lock_to_date"),
            ]
        )
        self.assertEqual(len(new_exception), 1)
        self.assertEqual(
            new_exception.company_lock_date, fields.Date.to_date("2900-01-15")
        )

    def test_10_draft_and_cancel_after_lock_to_date(self):
        """Posted entries after the lock to date can be neither reset to draft
        nor cancelled, unless the lock check is bypassed."""
        move = self.create_account_move("2900-02-01", self.sale_journal)
        move.action_post()
        self.company.sale_lock_to_date = "2900-01-01"
        with self.assertRaises(ValidationError):
            move.button_draft()
        with self.assertRaises(ValidationError):
            move.button_cancel()
        move.with_context(bypass_lock_check=BYPASS_LOCK_CHECK).button_draft()
        self.assertEqual(move.state, "draft")

    def test_11_user_fiscal_lock_to_date_per_journal(self):
        """The fiscal lock to date of a journal is the earliest applicable one."""
        self.company.write(
            {
                "sale_lock_to_date": "2900-01-01",
                "purchase_lock_to_date": "2900-02-01",
                "fiscalyear_lock_to_date": "2900-03-01",
                "hard_lock_to_date": "2900-04-01",
            }
        )
        get_lock = self.company._get_user_fiscal_lock_to_date
        self.assertEqual(get_lock(self.sale_journal), fields.Date.to_date("2900-01-01"))
        self.assertEqual(
            get_lock(self.purchase_journal), fields.Date.to_date("2900-02-01")
        )
        self.assertEqual(get_lock(self.bank_journal), fields.Date.to_date("2900-03-01"))
        self.company.write(
            {
                "sale_lock_to_date": False,
                "purchase_lock_to_date": False,
                "fiscalyear_lock_to_date": False,
                "hard_lock_to_date": False,
            }
        )
        self.assertFalse(get_lock(self.bank_journal))

    def test_12_lock_to_date_violations(self):
        """Violations of the hard lock to date, and no violation without date."""
        self.company.hard_lock_to_date = "2900-01-01"
        self.assertFalse(self.company._get_lock_to_date_violations(False))
        self.assertFalse(
            self.company._get_lock_to_date_violations(fields.Date.to_date("2800-01-01"))
        )
        violations = self.company._get_lock_to_date_violations(
            fields.Date.to_date("2900-01-01")
        )
        self.assertEqual(
            violations, [(fields.Date.to_date("2900-01-01"), "hard_lock_date")]
        )
        self.assertFalse(
            self.company._get_lock_to_date_violations(
                fields.Date.to_date("2900-01-01"), hard=False
            )
        )
        self.company.hard_lock_to_date = False
        self.assertFalse(self.company.hard_lock_to_date)
