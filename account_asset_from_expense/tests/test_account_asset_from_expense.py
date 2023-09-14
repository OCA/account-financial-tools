# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountAssetFromExpense(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.expense_sheet_model = cls.env["hr.expense.sheet"]
        cls.product_1 = cls.env.ref("product.product_delivery_01")
        # New Employee
        employee_home = cls.env["res.partner"].create({"name": "Employee Home Address"})
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Employee A", "address_home_id": employee_home.id}
        )
        # Profile normal asset
        cls.profile_asset = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "asset_product_item": True,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Room - 5 Years",
                "method_time": "year",
                "method_number": 5,
                "method_period": "year",
            }
        )

    def _create_expense(
        self,
        description,
        employee,
        product,
        amount,
        asset_profile=False,
        payment_mode="own_account",
        account=False,
    ):
        with Form(self.env["hr.expense"]) as expense:
            expense.name = description
            expense.employee_id = employee
            expense.product_id = product
            expense.unit_amount = amount
            expense.payment_mode = payment_mode
            if account:
                expense.account_id = account
            if asset_profile:
                expense.asset_profile_id = asset_profile
        expense = expense.save()
        expense.tax_ids = False  # Test no vat
        return expense

    def test_01_create_asset_from_expense(self):
        """Create asset from expenses post journal entry"""
        expense = self._create_expense(
            "Test - Room Office",
            self.employee,
            self.product_1,
            1000.0,
            asset_profile=self.profile_asset,
        )
        # check account and asset profile must be equal
        self.assertEqual(
            expense.account_id, self.company_data["default_account_assets"]
        )
        sheet_dict = expense.action_submit_expenses()
        sheet = self.expense_sheet_model.search([("id", "=", sheet_dict["res_id"])])
        sheet.action_submit_sheet()
        sheet.approve_expense_sheets()
        sheet.action_sheet_move_create()
        # check asset
        assets = (
            self.env["account.asset.line"]
            .search([("move_id", "=", sheet.account_move_id.id)])
            .mapped("asset_id")
        )
        self.assertEqual(sheet.account_move_id.asset_count, 1)
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets.state, "draft")
