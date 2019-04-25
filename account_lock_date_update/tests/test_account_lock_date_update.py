# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestAccountLockDateUpdate(TransactionCase):

    def setUp(self):
        super(TestAccountLockDateUpdate, self).setUp()
        self.company = self.env.ref('base.main_company')
        self.demo_user = self.env.ref('base.user_demo')
        self.adviser_group = self.env.ref('account.group_account_manager')
        self.UpdateLockDateUpdateObj = self.env[
            'account.update.lock_date'
        ].sudo(self.demo_user)

    def create_account_lock_date_update(self):
        return self.UpdateLockDateUpdateObj.create({
            'company_id': self.company.id,
        })

    def test_01_update_without_access(self):
        wizard = self.create_account_lock_date_update()
        wizard.write({
            'period_lock_date': '2000-01-01',
            'fiscalyear_lock_date': '2000-01-01',
        })
        self.demo_user.write({
            'groups_id': [(3, self.adviser_group.id)],
        })
        with self.assertRaises(UserError):
            wizard.sudo(self.demo_user.id).execute()

    def test_02_update_with_access(self):
        wizard = self.create_account_lock_date_update()
        wizard.write({
            'period_lock_date': '2000-02-01',
            'fiscalyear_lock_date': '2000-01-01',
        })
        self.demo_user.write({
            'groups_id': [(4, self.adviser_group.id)],
        })
        wizard.sudo(self.demo_user.id).execute()
        self.assertEqual(
            fields.Date.to_string(self.company.period_lock_date),
            '2000-02-01')
        self.assertEqual(
            fields.Date.to_string(self.company.fiscalyear_lock_date),
            '2000-01-01')
