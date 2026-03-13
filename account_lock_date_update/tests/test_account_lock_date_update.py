# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import new_test_user, users

from odoo.addons.base.tests.common import BaseCommon


class TestAccountLockDateUpdate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.adviser_group = cls.env.ref("account.group_account_manager")
        new_test_user(
            cls.env, login="test_lock_date_user", groups="account.group_account_manager"
        )

    @users("test_lock_date_user")
    def test_01_update_with_access(self):
        wizard = self.env["account.update.lock_date"].create(
            {"company_id": self.company.id}
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
        wizard.execute()
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
