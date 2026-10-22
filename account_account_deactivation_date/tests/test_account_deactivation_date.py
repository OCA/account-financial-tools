# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from freezegun import freeze_time

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountDeactivationDate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.account = cls.copy_account(
            cls.company_data["default_account_expense"].with_env(cls.env)
        )
        cls.counterpart = cls.company_data["default_account_revenue"]
        cls.journal = cls.company_data["default_journal_misc"]

    def _create_move(self, move_date):
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": move_date,
                "journal_id": self.journal.id,
                "line_ids": [
                    Command.create({"account_id": self.account.id, "debit": 100.0}),
                    Command.create(
                        {"account_id": self.counterpart.id, "credit": 100.0}
                    ),
                ],
            }
        )

    def _use_in_tax_distribution(self, account):
        tax = self.tax_sale_a.copy({"name": f"Tax on {account.code}"})
        tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        ).account_id = account

    @freeze_time("2026-06-15")
    def test_future_date_keeps_account_active(self):
        self.account.deactivation_date = "2026-07-01"
        self.assertFalse(self.account.deprecated)

        move = self._create_move("2026-06-30")
        move.action_post()
        self.assertEqual(move.state, "posted")

        late_move = self._create_move("2026-07-01")
        with self.assertRaisesRegex(UserError, "inactive since"):
            late_move.action_post()

    @freeze_time("2026-06-15")
    def test_reached_date_deprecates_account(self):
        self.account.deactivation_date = "2026-06-15"
        self.assertTrue(self.account.deprecated)
        active_accounts = self.env["account.account"].search(
            [("deprecated", "=", False)]
        )
        self.assertNotIn(self.account, active_accounts)

    @freeze_time("2026-06-15")
    def test_back_dated_entry_after_deactivation(self):
        self.account.deactivation_date = "2026-06-01"
        self.assertTrue(self.account.deprecated)

        move = self._create_move("2026-05-31")
        move.action_post()
        self.assertEqual(move.state, "posted")

        late_move = self._create_move("2026-06-01")
        with self.assertRaisesRegex(UserError, "inactive since"):
            late_move.action_post()

    @freeze_time("2026-06-15")
    def test_line_check_follows_accounting_date(self):
        self.account.deactivation_date = "2026-06-01"
        move = self._create_move("2026-05-31")
        move.line_ids._check_constrains_account_id_journal_id()

        move.date = "2026-06-02"
        with self.assertRaisesRegex(UserError, "inactive since"):
            move.line_ids._check_constrains_account_id_journal_id()

    @freeze_time("2026-06-15")
    def test_skip_deactivation_check_context(self):
        self.account.deactivation_date = "2026-07-01"
        move = self._create_move("2026-07-05")
        move.with_context(skip_account_deactivation_check=True).action_post()
        self.assertEqual(move.state, "posted")

    @freeze_time("2026-06-15")
    def test_legacy_deprecated_account_stays_blocked(self):
        self.env.cr.execute(
            "UPDATE account_account SET deprecated = TRUE WHERE id = %s",
            [self.account.id],
        )
        self.account.invalidate_recordset(["deprecated"])
        move = self._create_move("2026-05-31")
        with self.assertRaisesRegex(UserError, "deprecated"):
            move.action_post()

    def test_cron_deprecates_due_accounts(self):
        with freeze_time("2026-06-15"):
            self.account.deactivation_date = "2026-06-20"
            self.env["account.account"]._cron_deprecate_due_accounts()
            self.assertFalse(self.account.deprecated)
        with freeze_time("2026-06-20"):
            self.env["account.account"]._cron_deprecate_due_accounts()
            self.assertTrue(self.account.deprecated)
            self.assertEqual(self.account.deactivation_date, date(2026, 6, 20))

    def test_cron_logs_failure(self):
        with freeze_time("2026-06-15"):
            self.account.deactivation_date = "2026-06-20"
            self._use_in_tax_distribution(self.account)
        with (
            freeze_time("2026-06-20"),
            self.assertLogs(
                "odoo.addons.account_account_deactivation_date.models.account_account",
                level="WARNING",
            ),
        ):
            self.env["account.account"]._cron_deprecate_due_accounts()
        self.assertFalse(self.account.deprecated)
        self.assertTrue(
            any(
                "could not be deprecated" in body
                for body in self.account.message_ids.mapped("body")
            )
        )

    @freeze_time("2026-06-15")
    def test_clear_date_reactivates_account(self):
        self.account.deactivation_date = "2026-06-01"
        self.assertTrue(self.account.deprecated)
        self.account.deactivation_date = False
        self.assertFalse(self.account.deprecated)

    @freeze_time("2026-06-15")
    def test_deprecated_flag_does_not_set_date(self):
        scheduled = self.copy_account(self.account, {"deactivation_date": "2026-07-01"})
        self.account.deprecated = True
        scheduled.deprecated = True
        self.assertFalse(self.account.deactivation_date)
        self.assertEqual(scheduled.deactivation_date, date(2026, 7, 1))
        self.assertTrue(self.account.deprecated)
        move = self._create_move("2017-02-01")
        with self.assertRaisesRegex(UserError, "deprecated"):
            move.action_post()

    @freeze_time("2026-06-15")
    def test_create_syncs_deprecated(self):
        dated = self.copy_account(self.account, {"deactivation_date": "2026-06-01"})
        self.assertTrue(dated.deprecated)
        deprecated = self.copy_account(self.account, {"deprecated": True})
        self.assertFalse(deprecated.deactivation_date)
        self.assertTrue(deprecated.deprecated)

    @freeze_time("2026-06-15")
    def test_onchange_updates_deprecated(self):
        with Form(self.account) as account_form:
            account_form.deactivation_date = date(2026, 6, 1)
            self.assertTrue(account_form.deprecated)
            account_form.deactivation_date = date(2026, 7, 1)
            self.assertFalse(account_form.deprecated)
        self.assertEqual(self.account.deactivation_date, date(2026, 7, 1))
        self.assertFalse(self.account.deprecated)

    @freeze_time("2026-06-15")
    def test_date_before_posted_entries_rejected(self):
        self._create_move("2026-06-10").action_post()
        with self.assertRaisesRegex(ValidationError, "last posted journal item"):
            self.account.deactivation_date = "2026-06-10"
        self.account.deactivation_date = "2026-06-11"
        self.assertTrue(self.account.deprecated)

    @freeze_time("2026-06-15")
    def test_tax_distribution_rejected(self):
        self._use_in_tax_distribution(self.account)
        with self.assertRaisesRegex(ValidationError, "tax distribution"):
            self.account.deactivation_date = "2026-07-01"

    @freeze_time("2026-06-15")
    def test_deactivation_date_is_tracked(self):
        self.env.cr.precommit.run()
        self.account.with_context(
            tracking_disable=False, mail_notrack=False
        ).deactivation_date = "2026-07-01"
        self.env.flush_all()
        self.env.cr.precommit.run()
        tracking = self.account.message_ids.tracking_value_ids.filtered(
            lambda value: value.field_id.name == "deactivation_date"
        )
        self.assertTrue(tracking)
