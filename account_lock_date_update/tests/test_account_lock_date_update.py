# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAccountLockDateUpdate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.demo_user = cls.env.ref("base.user_demo")
        cls.adviser_group = cls.env.ref("account.group_account_manager")

    def test_01_update_without_access(self):
        self.demo_user.write({"groups_id": [Command.unlink(self.adviser_group.id)]})
        with self.assertRaises(AccessError):
            self.env["account.update.lock_date"].with_user(self.demo_user.id).create(
                {"company_id": self.company.id}
            )

    def test_02_update_with_access(self):
        self.demo_user.write({"groups_id": [Command.link(self.adviser_group.id)]})
        wizard = (
            self.env["account.update.lock_date"]
            .with_user(self.demo_user.id)
            .create({"company_id": self.company.id})
        )
        wizard.write(
            {
                "sale_lock_date": "2000-05-01",
                "purchase_lock_date": "2000-04-01",
                "tax_lock_date": "2000-03-01",
                "fiscalyear_lock_date": "2000-02-01",
                "hard_lock_date": "2000-01-01",
            }
        )
        wizard.with_user(self.demo_user.id).execute()
        self.assertEqual(
            fields.Date.to_string(self.company.sale_lock_date), "2000-05-01"
        )
        self.assertEqual(
            fields.Date.to_string(self.company.purchase_lock_date), "2000-04-01"
        )
        self.assertEqual(
            fields.Date.to_string(self.company.tax_lock_date), "2000-03-01"
        )
        self.assertEqual(
            fields.Date.to_string(self.company.fiscalyear_lock_date), "2000-02-01"
        )
        self.assertEqual(
            fields.Date.to_string(self.company.hard_lock_date), "2000-01-01"
        )

    def test_03_company_change_shows_its_lock_dates(self):
        other_company = self.env["res.company"].create(
            {"name": "Lock Date Other Company"}
        )
        other_company.write(
            {"sale_lock_date": "2001-05-31", "purchase_lock_date": "2001-04-30"}
        )
        self.company.write(
            {"sale_lock_date": "2000-05-01", "tax_lock_date": "2000-03-01"}
        )
        self.demo_user.write(
            {
                "company_ids": [Command.link(other_company.id)],
                "groups_id": [
                    Command.link(self.adviser_group.id),
                    Command.link(self.env.ref("base.group_multi_company").id),
                ],
            }
        )
        wizard_obj = (
            self.env["account.update.lock_date"]
            .with_user(self.demo_user)
            .with_context(allowed_company_ids=[self.company.id, other_company.id])
        )
        with Form(wizard_obj) as wizard_form:
            self.assertEqual(wizard_form.company_id, self.company)
            self.assertEqual(
                fields.Date.to_string(wizard_form.tax_lock_date), "2000-03-01"
            )
            wizard_form.company_id = other_company
            self.assertEqual(
                fields.Date.to_string(wizard_form.sale_lock_date), "2001-05-31"
            )
            self.assertEqual(
                fields.Date.to_string(wizard_form.purchase_lock_date), "2001-04-30"
            )
            self.assertFalse(wizard_form.tax_lock_date)
        wizard_form.record.execute()
        # nothing of the first company was written on the second one
        self.assertFalse(other_company.tax_lock_date)
        self.assertEqual(
            fields.Date.to_string(other_company.sale_lock_date), "2001-05-31"
        )
        self.assertEqual(
            fields.Date.to_string(self.company.tax_lock_date), "2000-03-01"
        )

    def test_04_company_of_another_user_refused(self):
        self.demo_user.write({"groups_id": [Command.link(self.adviser_group.id)]})
        foreign_company = self.env["res.company"].create(
            {"name": "Lock Date Foreign Company"}
        )
        self.assertNotIn(foreign_company, self.demo_user.company_ids)
        wizard = (
            self.env["account.update.lock_date"]
            .with_user(self.demo_user.id)
            .create({"company_id": foreign_company.id})
        )
        wizard.write({"sale_lock_date": "2000-05-01"})
        with self.assertRaises(UserError):
            wizard.with_user(self.demo_user.id).execute()
        self.assertFalse(foreign_company.sale_lock_date)

    def test_05_company_shown_to_multi_company_users(self):
        multi_company_group = self.env.ref("base.group_multi_company")
        self.demo_user.write({"groups_id": [Command.link(self.adviser_group.id)]})
        wizard_obj = self.env["account.update.lock_date"].with_user(self.demo_user)
        self.demo_user.write({"groups_id": [Command.unlink(multi_company_group.id)]})
        arch = wizard_obj.get_views([(False, "form")])["views"]["form"]["arch"]
        self.assertNotIn('name="company_id"', arch)
        self.demo_user.write({"groups_id": [Command.link(multi_company_group.id)]})
        arch = wizard_obj.get_views([(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="company_id"', arch)
