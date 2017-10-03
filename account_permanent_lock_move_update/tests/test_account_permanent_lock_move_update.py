# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestPermanentLockMoveUpdate(TransactionCase):

    def setUp(self):
        super(TestPermanentLockMoveUpdate, self).setUp()
        self.PermanentLockMove = self.env['permanent.lock.date.wizard']

        self.company = self.env.ref('base.main_company')
        self.demo_user = self.env.ref('base.user_demo')
        self.adviser_group = self.env.ref('account.group_account_manager')

    def create_permanent_lock_move(self):
        return self.PermanentLockMove.create({
            'company_id': self.company.id,
        })

    def test_01_update_without_access(self):
        wizard = self.create_permanent_lock_move()
        wizard.write({
            'lock_date': '2000-01-01',
        })

        self.demo_user.write({
            'groups_id': [(3, self.adviser_group.id)],
        })

        with self.assertRaises(AccessError):
            wizard.sudo(self.demo_user.id).confirm_date()

    def test_02_update_with_access(self):
        wizard = self.create_permanent_lock_move()
        wizard.write({
            'lock_date': '2000-01-01',
        })

        self.demo_user.write({
            'groups_id': [(4, self.adviser_group.id)],
        })

        wizard.sudo(self.demo_user.id).confirm_date()
        self.assertEqual(self.company.permanent_lock_date, wizard.lock_date)
