# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.account_spread_cost_revenue.tests.test_account_invoice_spread import (
    TestAccountInvoiceSpread,
)


class TestAccountInvoiceSpreadEnhanced(TestAccountInvoiceSpread):
    def setUp(self):
        super().setUp()
        self.wizard = self.env["account.spread.invoice.line.link.wizard"]
        self.wizard_spread_link = self.env["account.spread.link.move.line"]

    def test_01_check_account_spread(self):
        with self.assertRaises(UserError):
            with Form(self.spread) as spread:
                spread.create_move_type = "in_invoice"
        with Form(self.spread) as spread:
            spread.debit_account_id = self.account_payable
            spread.create_move_type = "in_invoice"
        # Create invoice spread cost from vendor bills
        wizard1 = self.wizard.with_context(
            default_invoice_line_id=self.vendor_bill_line.id,
            default_company_id=self.env.company.id,
            allow_spread_planning=True,
        ).create({"spread_action_type": "link", "spread_id": self.spread.id})
        result = wizard1.confirm()
        # Compute lines in spread cost
        spread = self.env["account.spread"].browse(result["res_id"])
        spread.compute_spread_board()
        spread_lines = spread.line_ids
        # Check lines created must be move type in_invoice
        for line in spread_lines:
            line.create_move()
            self.assertEqual(line.move_id.move_type, "in_invoice")
        with Form(self.wizard_spread_link.with_context(active_id=spread.id)) as wiz:
            wiz.move_id = spread_lines[0].move_id
            wiz.move_line_id = spread_lines[0].move_id.line_ids[0]
        wizard_spread_link = wiz.save()
        # Already linked
        with self.assertRaises(UserError):
            wizard_spread_link.link_move_line()
        wizard_spread_link.with_context(active_id=False).link_move_line()
