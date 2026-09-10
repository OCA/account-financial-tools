# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountAssetManagementStockLot(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Models
        cls.asset_model = cls.env["account.asset"]
        cls.lot_model = cls.env["stock.lot"]
        # Existing instances
        cls.asset_profile = cls.env["account.asset.profile"].create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Hardware - 3 Years",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        # Instances
        cls.product_serial = cls.env["product.product"].create(
            {"name": "Serial Product", "is_storable": True, "tracking": "serial"}
        )
        cls.product_lot = cls.env["product.product"].create(
            {"name": "Lot Product", "is_storable": True, "tracking": "lot"}
        )
        cls.serial = cls.lot_model.create(
            {
                "name": "SN-001",
                "product_id": cls.product_serial.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.lot = cls.lot_model.create(
            {
                "name": "L-100",
                "product_id": cls.product_lot.id,
                "company_id": cls.env.company.id,
            }
        )

    @classmethod
    def _create_asset(cls, **kwargs):
        vals = {
            "name": "Test Asset",
            "profile_id": cls.asset_profile.id,
            "purchase_value": 1000.0,
            "date_start": "2024-01-01",
            "method_time": "year",
            "method_number": 3,
            "method_period": "year",
        }
        vals.update(kwargs)
        return cls.asset_model.create(vals)

    def test_compute_product_id(self):
        asset = self._create_asset(stock_lot_id=self.serial.id)
        self.assertEqual(asset.product_id, self.product_serial)

    def test_serial_lot_unique_asset(self):
        self._create_asset(stock_lot_id=self.serial.id)
        with self.assertRaises(UserError):
            self._create_asset(stock_lot_id=self.serial.id)

    def test_lot_allows_multiple_assets(self):
        asset_1 = self._create_asset(stock_lot_id=self.lot.id)
        asset_2 = self._create_asset(stock_lot_id=self.lot.id)
        self.assertEqual(asset_1.product_id, self.product_lot)
        self.assertEqual(asset_2.product_id, self.product_lot)
