# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import AccountAccountUsedCommon


@tagged("post_install", "-at_install")
class TestAccountAccountUsed(AccountAccountUsedCommon):
    def test_draft_move_does_not_use_account(self):
        self._create_move(self.account)
        self.assertFalse(self.account.is_used_in_posted_move)

    def test_posted_move_uses_account(self):
        self._create_move(self.account, post=True)
        accounts = self.account | self.other_account
        self.assertEqual(accounts._get_used_in_posted_moves(), self.account)
        self.assertTrue(self.account.is_used_in_posted_move)
        self.assertFalse(self.other_account.is_used_in_posted_move)
