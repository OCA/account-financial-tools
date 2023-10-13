# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import AccessError
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
        self.demo_user.write({"groups_id": [(3, self.adviser_group.id)]})
        with self.assertRaises(AccessError):
            self.env["account.update.lock_date"].with_user(self.demo_user.id).create(
                {"company_id": self.company.id}
            )

    def test_02_update_with_access(self):
        self.demo_user.write({"groups_id": [(4, self.adviser_group.id)]})
        wizard = (
            self.env["account.update.lock_date"]
            .with_user(self.demo_user.id)
            .create({"company_id": self.company.id})
        )
        wizard.write(
            {
                "period_lock_date": "2000-02-01",
                "fiscalyear_lock_date": "2000-01-01",
                "tax_lock_date": "2000-01-01",
            }
        )
        wizard.with_user(self.demo_user.id).execute()
        self.assertEqual(
            fields.Date.to_string(self.company.period_lock_date), "2000-02-01"
        )
        self.assertEqual(
            fields.Date.to_string(self.company.fiscalyear_lock_date), "2000-01-01"
        )
        self.assertEqual(
            fields.Date.to_string(self.company.tax_lock_date), "2000-01-01"
        )
