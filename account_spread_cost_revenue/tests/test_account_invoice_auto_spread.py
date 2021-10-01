# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .test_account_invoice_spread import TestAccountInvoiceSpread


class TestAccountInvoiceAutoSpread(TestAccountInvoiceSpread):
    def test_01_no_auto_spread_sheet(self):

        self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "purchase",
                "period_number": 5,
                "period_type": "month",
                "spread_account_id": self.account_payable.id,
                "spread_journal_id": self.expenses_journal.id,
                "auto_spread": False,  # Auto Spread = False
                "auto_spread_ids": [
                    (0, 0, {"account_id": self.vendor_bill_line.account_id.id})
                ],
            }
        )

        self.assertFalse(self.vendor_bill_line.spread_id)
        self.vendor_bill.action_post()
        self.assertFalse(self.vendor_bill_line.spread_id)

    def test_02_new_auto_spread_sheet_purchase(self):

        self.env["account.spread.template"].create(
            {
                "name": "test 1",
                "spread_type": "purchase",
                "period_number": 5,
                "period_type": "month",
                "spread_account_id": self.account_payable.id,
                "spread_journal_id": self.expenses_journal.id,
                "auto_spread": True,  # Auto Spread
                "auto_spread_ids": [
                    (0, 0, {"account_id": self.vendor_bill_line.account_id.id})
                ],
            }
        )
        template2 = self.env["account.spread.template"].create(
            {
                "name": "test 2",
                "spread_type": "purchase",
                "period_number": 5,
                "period_type": "month",
                "spread_account_id": self.account_payable.id,
                "spread_journal_id": self.expenses_journal.id,
                "auto_spread": True,  # Auto Spread
                "auto_spread_ids": [
                    (0, 0, {"account_id": self.vendor_bill_line.account_id.id})
                ],
            }
        )
        template2._check_auto_spread_ids_unique()

        self.assertFalse(self.vendor_bill_line.spread_id)
        with self.assertRaises(UserError):  # too many auto_spread_ids matched
            self.vendor_bill.action_post()

        template2.auto_spread = False  # Do not use this template
        self.vendor_bill.action_post()
        self.assertTrue(self.vendor_bill_line.spread_id)

        spread_lines = self.vendor_bill_line.spread_id.line_ids
        self.assertTrue(spread_lines)

        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

    def test_03_new_auto_spread_sheet_sale(self):

        self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "sale",
                "period_number": 5,
                "period_type": "month",
                "spread_account_id": self.account_receivable.id,
                "spread_journal_id": self.sales_journal.id,
                "auto_spread": True,  # Auto Spread
                "auto_spread_ids": [
                    (0, 0, {"account_id": self.invoice_line.account_id.id})
                ],
            }
        )

        self.assertFalse(self.invoice_line.spread_id)
        self.sale_invoice.action_post()
        self.assertTrue(self.invoice_line.spread_id)

        spread_lines = self.invoice_line.spread_id.line_ids
        self.assertTrue(spread_lines)

        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)
