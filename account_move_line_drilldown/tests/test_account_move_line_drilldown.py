# Copyright 2021 Opener B.V. <stefan@opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import SavepointCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMoveLineDrilldown(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.env.user.company_id.id)], limit=1)
        cls.accounts = cls.env["account.account"].search(
            [("company_id", "=", cls.env.user.company_id.id)], limit=3)
        cls.group1 = cls.env["account.group"].create({
            "name": "1",
            "code_prefix": "1",
        })
        cls.group12 = cls.env["account.group"].create({
            "name": "12",
            "code_prefix": "12",
            "parent_id": cls.group1.id,
        })
        cls.group123 = cls.env["account.group"].create({
            "name": "123",
            "code_prefix": "123",
            "parent_id": cls.group12.id,
        })
        cls.group124 = cls.env["account.group"].create({
            "name": "124",
            "code_prefix": "124",
            "parent_id": cls.group12.id,
        })
        cls.group15 = cls.env["account.group"].create({
            "name": "15",
            "code_prefix": "15",
            "parent_id": cls.group1.id,
        })
        cls.group156 = cls.env["account.group"].create({
            "name": "156",
            "code_prefix": "156",
            "parent_id": cls.group15.id,
        })

    def test_account_move_line_drilldown(self):
        """Fields from this module are computed as expected"""
        move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {'debit': 100.0, 'account_id': self.accounts[0].id}),
                (0, 0, {'credit': 100.0, 'account_id': self.accounts[1].id}),
            ],
        })
        move_line = move.line_ids[0]
        account = move_line.account_id
        account.group_id = self.group123
        self.assertEqual(move_line.account_root_group_id, self.group1)
        self.assertEqual(move_line.account_sub_group_id, self.group12)

        account.group_id = self.group12
        self.assertEqual(move_line.account_root_group_id, self.group1)
        self.assertEqual(move_line.account_sub_group_id, self.group12)

        account.group_id = self.group1
        self.assertEqual(move_line.account_root_group_id, self.group1)
        self.assertFalse(move_line.account_sub_group_id)

        account.group_id = self.group156
        self.assertEqual(move_line.account_root_group_id, self.group1)
        self.assertEqual(move_line.account_sub_group_id, self.group15)

        self.group156.parent_id = self.group123
        self.assertEqual(move_line.account_root_group_id, self.group1)
        self.assertEqual(move_line.account_sub_group_id, self.group12)

        self.group156.parent_id = False
        self.assertEqual(move_line.account_root_group_id, self.group156)
        self.assertFalse(move_line.account_sub_group_id)
