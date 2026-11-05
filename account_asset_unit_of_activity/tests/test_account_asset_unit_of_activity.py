# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAssetUnitOfActivity(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        # Only the profile needed by the unit of activity tests is created:
        # inheriting account_asset_management TestAssetManagement would replay
        # the whole account_asset_management test suite under this module.
        cls.uoa_profile = cls.asset_profile_model.create(
            {
                "name": "Hardware - Unit of Activity",
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "method": "unit-activity",
                "method_time": "year",
                "method_number": 1,
                "method_period": "year",
                "total_number_of_use": 100,
            }
        )

    def _create_uoa_asset(self, purchase_value=10000.0, total_number_of_use=100):
        return self.asset_model.create(
            {
                "name": "Asset unit of activity",
                "profile_id": self.uoa_profile.id,
                "purchase_value": purchase_value,
                "date_start": "2025-01-01",
                "method": "unit-activity",
                "method_time": "year",
                "method_number": 1,
                "method_period": "year",
                "total_number_of_use": total_number_of_use,
            }
        )

    def _add_usage(self, asset, quantity, usage_date):
        wizard = (
            self.env["account.asset.unit.of.activity"]
            .with_context(active_id=asset.id)
            .create({"quantity": quantity, "date": usage_date})
        )
        return wizard.add_usage()

    def test_01_compute_depreciation_board_is_skipped(self):
        asset = self._create_uoa_asset()
        asset.compute_depreciation_board()
        self.assertFalse(
            asset.depreciation_line_ids.filtered(lambda line: line.type == "depreciate")
        )

    def test_02_add_usage(self):
        asset = self._create_uoa_asset()
        self.assertEqual(asset.remaining_usage, 100)
        self._add_usage(asset, 10, "2025-02-01")
        asset.invalidate_recordset()
        self.assertEqual(asset.remaining_usage, 90)
        line = asset.depreciation_line_ids.filtered(
            lambda line: line.type == "depreciate"
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.quantity, 10)
        self.assertEqual(line.amount, 1000.0)
        self.assertEqual(line.remaining_value, 9000.0)
        self.assertEqual(line.depreciated_value, 0.0)

    def test_03_last_usage_takes_the_residual_value(self):
        asset = self._create_uoa_asset(purchase_value=1000.0, total_number_of_use=3)
        self._add_usage(asset, 1, "2025-02-01")
        self._add_usage(asset, 1, "2025-03-01")
        self._add_usage(asset, 1, "2025-04-01")
        asset.invalidate_recordset()
        self.assertEqual(asset.remaining_usage, 0)
        lines = asset.depreciation_line_ids.filtered(
            lambda line: line.type == "depreciate"
        ).sorted("line_date")
        self.assertEqual(len(lines), 3)
        self.assertEqual(sum(lines.mapped("amount")), 1000.0)
        self.assertEqual(lines[-1].remaining_value, 0.0)

    def test_04_add_usage_with_move(self):
        asset = self._create_uoa_asset()
        asset.validate()
        self.assertEqual(asset.state, "open")
        wizard = (
            self.env["account.asset.unit.of.activity"]
            .with_context(active_id=asset.id)
            .create(
                {
                    "quantity": 10,
                    "date": "2025-02-01",
                    "auto_create_asset_move": True,
                }
            )
        )
        wizard.add_usage()
        asset.invalidate_recordset()
        line = asset.depreciation_line_ids.filtered(
            lambda line: line.type == "depreciate"
        )
        self.assertTrue(line.move_id)
        self.assertEqual(line.move_id.state, "posted")
        self.assertEqual(asset.value_residual, 9000.0)

    def test_05_total_number_of_use_can_not_be_null(self):
        asset = self._create_uoa_asset()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            asset.write({"total_number_of_use": 0})

    def test_06_date_must_respect_the_chronology(self):
        asset = self._create_uoa_asset()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._add_usage(asset, 1, "2024-12-01")
        self._add_usage(asset, 1, "2025-02-01")
        with self.assertRaises(UserError), self.cr.savepoint():
            self._add_usage(asset, 1, "2025-01-15")

    def test_07_quantity_can_not_exceed_remaining_usage(self):
        asset = self._create_uoa_asset()
        with self.assertRaises(UserError), self.cr.savepoint():
            self._add_usage(asset, 101, "2025-02-01")
