# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..models.account_account import CHECK_ACCOUNT_NAME_UNIQUE_PARAM


@tagged("post_install", "-at_install")
class TestAccountAccountNameUnique(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls._create_account("999001", "Unique 100% label")

    @classmethod
    def _create_account(cls, code, name):
        return cls.env["account.account"].create(
            {"code": code, "name": name, "account_type": "income"}
        )

    def _enable_check(self):
        self.env["ir.config_parameter"].sudo().set_param(
            CHECK_ACCOUNT_NAME_UNIQUE_PARAM, True
        )

    def test_check_disabled(self):
        self._create_account("999002", "unique 100% LABEL")

    def test_check_enabled(self):
        self._enable_check()
        with self.assertRaises(ValidationError):
            self._create_account("999002", "unique 100% LABEL")
        other = self._create_account("999004", "Other label")
        with self.assertRaises(ValidationError):
            other.name = "Unique 100% label"

    def test_check_enabled_other_company(self):
        other_company = self.setup_other_company()["company"]
        self._enable_check()
        self.env["account.account"].with_company(other_company).create(
            {
                "code": "999002",
                "name": "Unique 100% label",
                "account_type": "income",
                "company_ids": [(6, 0, other_company.ids)],
            }
        )

    def test_enable_setting_with_duplicates(self):
        duplicate = self._create_account("999002", "Unique 100% label")
        settings = self.env["res.config.settings"].create(
            {"check_account_name_unique": True}
        )
        duplicates = self.env["account.account"]._get_duplicate_name_accounts()
        self.assertIn(self.account, duplicates)
        self.assertIn(duplicate, duplicates)
        with self.assertRaisesRegex(UserError, "have the same label"):
            settings.execute()
