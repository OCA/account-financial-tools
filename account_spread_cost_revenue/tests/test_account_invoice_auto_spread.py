# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .test_account_invoice_spread import TestAccountInvoiceSpread


@tagged("post_install", "-at_install")
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

    def test_04_new_auto_spread_sheet_sale_refund(self):
        refund = self.create_account_invoice(invoice_type="out_refund")
        refund.invoice_date = fields.Date.today()
        refund_line = refund.invoice_line_ids
        self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "sale",
                "period_number": 5,
                "period_type": "month",
                "spread_account_id": self.account_receivable.id,
                "spread_journal_id": self.sales_journal.id,
                "auto_spread": True,  # Auto Spread
                "auto_spread_ids": [(0, 0, {"account_id": refund_line.account_id.id})],
            }
        )
        revenue_account = refund_line.account_id
        refund.action_post()
        spread = refund_line.spread_id
        self.assertEqual(spread.invoice_type, "out_refund")
        self.assertEqual(spread.debit_account_id, revenue_account)
        self.assertEqual(spread.credit_account_id, self.account_receivable)
        self.assertEqual(refund_line.account_id, self.account_receivable)
        for line in spread.line_ids:
            line.create_move()
            self.assertTrue(line.move_id)

    def test_05_new_auto_spread_sheet_purchase_refund(self):
        refund = self.create_account_invoice(invoice_type="in_refund")
        refund.invoice_date = fields.Date.today()
        refund_line = refund.invoice_line_ids
        self.env["account.spread.template"].create(
            {
                "name": "test",
                "spread_type": "purchase",
                "period_number": 5,
                "period_type": "month",
                "spread_account_id": self.account_payable.id,
                "spread_journal_id": self.expenses_journal.id,
                "auto_spread": True,  # Auto Spread
                "auto_spread_ids": [(0, 0, {"account_id": refund_line.account_id.id})],
            }
        )
        expense_account = refund_line.account_id
        refund.action_post()
        spread = refund_line.spread_id
        self.assertEqual(spread.invoice_type, "in_refund")
        self.assertEqual(spread.debit_account_id, self.account_payable)
        self.assertEqual(spread.credit_account_id, expense_account)
        self.assertEqual(refund_line.account_id, self.account_payable)
        for line in spread.line_ids:
            line.create_move()
            self.assertTrue(line.move_id)
