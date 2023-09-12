from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveLineLandedCostInfo(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.stock_landed_cost = cls.env["stock.landed.cost"].create({})

        cls.adjustment_line = cls.env["stock.valuation.adjustment.lines"].create(
            {
                "name": "test",
                "product_id": cls.product_a.id,
                "additional_landed_cost": 10,
                "cost_id": cls.stock_landed_cost.id,
            }
        )

    def test_create_account_move_line(self):
        AccMoveLines = self.adjustment_line._create_account_move_line(
            0,
            self.product_a.property_account_expense_id.id,
            self.product_a.property_account_expense_id.id,
            0,
            0,
        )
        for lines in AccMoveLines:
            if isinstance(lines, list) and isinstance(lines[2], dict):
                if "debit" in lines[2]:
                    self.assertEqual(lines[2]["debit"], 10.0)

                elif "credit" in lines[2]:
                    self.assertEqual(lines[2]["credit"], 10.0)

                self.assertEqual(
                    lines[2]["stock_valuation_adjustment_line_id"],
                    self.adjustment_line.id,
                )
                self.assertEqual(
                    lines[2]["stock_landed_cost_id"], self.adjustment_line.cost_id.id
                )
