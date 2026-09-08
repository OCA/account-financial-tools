# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


@tagged("post_install", "-at_install")
class TestAccountMoveLineRepairInfo(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_inventory = cls.env["account.account"].create(
            {
                "name": "Inventory Account",
                "code": "100101",
                "account_type": "asset_current",
            }
        )
        cls.warehouse.repair_type_id.default_location_dest_id.valuation_account_id = (
            cls.account_inventory
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_fifo_auto, cls.warehouse.lot_stock_id, 5
        )

    def _create_repair(self):
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product.id,
                "partner_id": self.owner.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "repair_line_type": "add",
                            "product_id": self.product_fifo_auto.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()
        return repair

    def test_repair_order_on_valuation_entry(self):
        repair = self._create_repair()
        account_move = repair.move_ids.account_move_id
        self.assertTrue(account_move)
        self.assertEqual(
            account_move.line_ids.mapped("repair_order_id"),
            repair,
        )

    def test_repair_order_journal_items(self):
        repair = self._create_repair()
        self.assertEqual(
            repair.account_move_line_ids,
            repair.move_ids.account_move_id.line_ids,
        )
