# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAssetLowValue(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.remove_model = cls.env["account.asset.remove"]
        # Low value asset profile
        expense_account = cls.company_data["default_account_expense"]
        cls.profile_low_value = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": expense_account.id,
                "account_asset_id": expense_account.id,
                "account_depreciation_id": expense_account.id,
                "account_residual_value_id": expense_account.id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Asset Low Value",
                "method_time": "year",
                "method_number": 0,
                "method_period": "year",
            }
        )

        # Invoice
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test", "standard_price": 500.0}
        )
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="in_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(cls.env.user)
        move_form.partner_id = cls.partner
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.product_id = cls.product
            line_form.price_unit = 2000.00
            line_form.quantity = 1
        cls.invoice = move_form.save()

    def test_01_asset_low_value(self):
        invoice = self.invoice
        move_form = Form(invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.asset_profile_id = self.profile_low_value
        invoice = move_form.save()
        invoice.action_post()
        asset = invoice.invoice_line_ids.mapped("asset_id")
        move_count = len(asset.account_move_line_ids)
        self.assertTrue(asset.low_value)
        asset.validate()

        self.assertEqual(asset.value_residual, 0)
        self.assertEqual(asset.state, "open")
        asset.remove()
        remove_model = self.env["account.asset.remove"].with_context(active_id=asset.id)
        with Form(remove_model) as f:
            f.posting_regime = "residual_value"
        remove = f.save()
        remove.remove()
        self.assertEqual(asset.state, "removed")
        self.assertEqual(
            len(asset.account_move_line_ids), move_count
        )  # no new account moves
        # Search test
        low_value_assets = self.asset_model.search([("low_value", "=", True)])
        self.assertIn(asset, low_value_assets)
        normal_assets = self.asset_model.search([("low_value", "!=", True)])
        self.assertNotIn(asset, normal_assets)
