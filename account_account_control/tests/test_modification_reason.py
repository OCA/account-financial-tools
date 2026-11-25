# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.account_account import REQUIRE_MODIFICATION_REASON_PARAM
from .common import AccountAccountUsedCommon


@tagged("post_install", "-at_install")
class TestAccountAccountModificationReason(AccountAccountUsedCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            REQUIRE_MODIFICATION_REASON_PARAM, True
        )
        cls.reason = cls.env["account.account.modification.reason"].create(
            {"name": "Chart of accounts review"}
        )
        cls._create_move(cls.account, post=True)
        # Records created in the current transaction are not tracked
        cls.env.cr.precommit.run()
        cls.account = cls.account.with_context(
            tracking_disable=False, mail_notrack=False
        )

    def _get_last_tracked_fields(self):
        self.env.cr.precommit.run()
        message = self.account.message_ids.sorted("id")[-1:]
        return message.tracking_value_ids.field_id.mapped("name")

    def test_option_disabled(self):
        self.env["ir.config_parameter"].sudo().set_param(
            REQUIRE_MODIFICATION_REASON_PARAM, False
        )
        self.assertFalse(self.account.is_modification_reason_required)
        self.account.name = "New name"
        self.assertEqual(self.account.name, "New name")

    def test_account_without_reason(self):
        for account in self.account | self.other_account:
            self.assertTrue(account.is_modification_reason_required)
            with self.assertRaisesRegex(UserError, "modification reason is required"):
                account.name = "New name"

    def test_account_create_without_reason(self):
        account = self._create_test_account("999003", "Test account 3")
        # The modification reason is still required after the creation
        with self.assertRaisesRegex(UserError, "modification reason is required"):
            account.name = "New name"

    def test_account_technical_update_without_reason(self):
        for key in ("install_mode", "chart_template_load"):
            self.account.with_context(**{key: True}).note = key
            self.assertEqual(self.account.note, key)

    def test_account_sudo_or_skip(self):
        self.account.sudo().name = "New name"
        self.account.with_context(skip_account_modification_reason=True).note = "Note"
        self.assertEqual(self.account.name, "New name")
        self.assertEqual(self.account.note, "Note")

    def test_account_reason_tracked(self):
        self.account.write(
            {"name": "New name", "modification_reason_id": self.reason.id}
        )
        self.assertEqual(self.account.modification_reason_id, self.reason)
        self.assertEqual(
            sorted(self._get_last_tracked_fields()),
            ["modification_reason_id", "name"],
        )

    def test_account_same_reason_tracked(self):
        self.account.write(
            {"name": "New name", "modification_reason_id": self.reason.id}
        )
        self._get_last_tracked_fields()
        self.account.write({"note": "Note", "modification_reason_id": self.reason.id})
        self.assertEqual(
            sorted(self._get_last_tracked_fields()),
            ["modification_reason_id", "note"],
        )
