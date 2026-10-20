# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAccountAutoCode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test account type
        cls.account_type = cls.env["account.account"].create(
            {
                "name": "Test Account Type",
                "code": "TEST",
                "account_type": "asset_current",
            }
        )
        # Note: testing account.account fields typically require valid account
        # architectures, but we focus mainly on the auto increment code behavior
        # given an account_type

    def create_account(self, code, acc_type="asset_current"):
        return self.env["account.account"].create(
            {
                "name": f"Account {code}",
                "code": code,
                "account_type": acc_type,
            }
        )

    def test_01_numeric_increment(self):
        """Test numeric code increment (e.g., 100 -> 101)"""
        # We use a very high number to ensure it's the max for the test
        unique_code = "989898"
        self.create_account(unique_code, "liability_current")

        # Calling onchange to verify automatic generation
        account_new = self.env["account.account"].new(
            {"name": "New Acct", "account_type": "liability_current"}
        )
        account_new._onchange_account_type_set_code()

        self.assertEqual(
            account_new.code,
            "989899",
            "Should increment purely numeric code correctly",
        )

    def test_02_alphanumeric_increment(self):
        """Test alphanumeric code increment (e.g., A100B -> A101B)"""
        unique_code = "UNIQUE989898X"
        self.create_account(unique_code, "income_other")
        acc_other = self.env["account.account"].new(
            {"name": "New Acct", "account_type": "income_other"}
        )
        acc_other._onchange_account_type_set_code()
        self.assertEqual(
            acc_other.code,
            "UNIQUE989899X",
            "Should extract and increment the numeric part properly",
        )

    def test_03_error_on_no_numeric_part(self):
        """Test that ValidationError is raised if the account type has no
        numeric parts in its codes"""
        self.create_account("BANK", "expense_depreciation")

        with self.assertRaises(ValidationError) as e:
            acc_new = self.env["account.account"].new(
                {
                    "name": "New Error Acct",
                    "account_type": "expense_depreciation",
                }
            )
            acc_new._onchange_account_type_set_code()

        self.assertIn(
            "Cannot increment code because no numeric part found",
            str(e.exception),
            "Should raise specific ValidationError when code has no numbers",
        )

    def test_04_skip_generation_if_no_codes(self):
        """Test if it falls back correctly if no codes exist"""
        next_code = self.env["account.account"]._get_next_account_code("some_fake_type")
        self.assertFalse(
            next_code, "Should return False if no codes exist for that type"
        )
