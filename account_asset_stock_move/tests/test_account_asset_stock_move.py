# Copyright 2021 Ecosoft Co., Ltd. <http://ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common
from odoo.tests.common import Form


class TestAccountAssetStockMove(common.TransactionCase):
    def setUp(self):
        super(TestAccountAssetStockMove, self).setUp()
        # Asset Profile
        self.account_expense = self.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_expenses").id,
                )
            ],
            limit=1,
        )
        self.account_asset = self.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_current_assets").id,
                )
            ],
            limit=1,
        )
        self.journal_purchase = self.env["account.journal"].search(
            [("type", "=", "purchase")], limit=1
        )
        self.asset_profile = self.env["account.asset.profile"].create(
            {
                "account_expense_depreciation_id": self.account_expense.id,
                "account_asset_id": self.account_asset.id,
                "account_depreciation_id": self.account_asset.id,
                "journal_id": self.journal_purchase.id,
                "name": "Furniture - 3 Years",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        # Realtime valuation product
        self.product_categ = self.env.ref("product.product_category_5")
        self.product_categ.property_valuation = "real_time"
        self.product_categ.property_stock_valuation_account_id = self.account_asset
        self.product_desk = self.env.ref("product.product_product_4d")
        self.product_desk.categ_id = self.product_categ
        self.picking_type_in = self.env.ref("stock.picking_type_in")

    def test_account_asset_stock_move(self):
        """Create Picking In with realtime valuation product,
        If account_asset_id in account move, asset profile will be set,
        and asset will be created when stock move is done"""
        with Form(self.env["stock.picking"]) as f:
            f.picking_type_id = self.picking_type_in
            with f.move_ids_without_package.new() as line:
                line.product_id = self.product_desk
                line.product_uom_qty = 1
        picking = f.save()
        picking.action_confirm()
        picking.move_lines[0].quantity_done = 1
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        move = self.env["account.move"].search(
            [("stock_move_id", "=", picking.move_lines[0].id)]
        )
        move_line = move.line_ids.filtered(lambda l: l.debit)
        self.assertEqual(move_line.account_id, self.account_asset)
        self.assertEqual(picking.asset_count, 1)
        res = picking.action_view_assets()
        asset = self.env[res["res_model"]].browse(res["res_id"])
        self.assertEqual(asset.profile_id, self.asset_profile)
