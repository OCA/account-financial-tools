# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.account_account import LOCK_USED_ACCOUNT_CODE_PARAM
from .common import AccountAccountUsedCommon


@tagged("post_install", "-at_install")
class TestAccountAccountCodeLock(AccountAccountUsedCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            LOCK_USED_ACCOUNT_CODE_PARAM, True
        )

    def test_change_code_unused_account(self):
        self._create_move(self.account)
        self.assertFalse(self.account.is_code_locked)
        self.account.code = "999101"
        self.assertEqual(self.account.code, "999101")

    def test_change_code_used_account(self):
        self._create_move(self.account, post=True)
        self.assertTrue(self.account.is_code_locked)
        with self.assertRaisesRegex(UserError, "used in posted journal entries"):
            self.account.code = "999101"

    def test_change_code_used_account_through_code_store(self):
        self._create_move(self.account, post=True)
        with self.assertRaisesRegex(UserError, "used in posted journal entries"):
            self.account.with_company(self.env.company.root_id).code_store = "999101"

    def test_write_same_code_used_account(self):
        self._create_move(self.account, post=True)
        self.account.write({"code": self.account.code, "name": "New name"})
        self.assertEqual(self.account.name, "New name")

    def test_change_code_used_account_lock_disabled(self):
        self.env["ir.config_parameter"].sudo().set_param(
            LOCK_USED_ACCOUNT_CODE_PARAM, False
        )
        self._create_move(self.account, post=True)
        self.assertFalse(self.account.is_code_locked)
        self.account.code = "999101"
        self.assertEqual(self.account.code, "999101")
