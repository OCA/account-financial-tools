from odoo import fields
from odoo.tests import TransactionCase


class TestWriteoffCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.income_account = cls.env["account.account"].create(
            {
                "name": "Test Write-off Income",
                "code": "TWOI",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )
        cls.expense_account = cls.env["account.account"].create(
            {
                "name": "Test Write-off Expense",
                "code": "TWOE",
                "account_type": "expense",
                "company_id": cls.company.id,
            }
        )
        cls.writeoff_journal = cls.env["account.journal"].create(
            {
                "name": "Test Write-off Journal",
                "code": "TWOJ",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.company.write(
            {
                "writeoff_threshold_amount": 10.0,
                "writeoff_income_account_id": cls.income_account.id,
                "writeoff_expense_account_id": cls.expense_account.id,
                "writeoff_journal_id": cls.writeoff_journal.id,
                "writeoff_batch_size": 50,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner WO"})
        cls.sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.bank_journal = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", cls.company.id)], limit=1
        )

    def _create_posted_invoice(self, move_type="out_invoice", amount=100.0):
        """Create and post a simple invoice/bill."""
        journal = (
            self.sale_journal
            if move_type in ("out_invoice", "out_refund")
            else self.purchase_journal
        )
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner.id,
                "journal_id": journal.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (0, 0, {"name": "Test line", "quantity": 1, "price_unit": amount})
                ],
            }
        )
        move.action_post()
        return move

    def _partial_pay(self, move, paid_amount):
        """Register a partial payment leaving a residual on the invoice."""
        is_customer = move.move_type in ("out_invoice", "out_refund")
        payment = self.env["account.payment"].create(
            {
                "amount": paid_amount,
                "payment_type": "inbound" if is_customer else "outbound",
                "partner_type": "customer" if is_customer else "supplier",
                "partner_id": self.partner.id,
                "journal_id": self.bank_journal.id,
            }
        )
        payment.action_post()
        invoice_line = move.line_ids.filtered(
            lambda line: line.account_id.account_type
            in ("asset_receivable", "liability_payable")
        )
        payment_line = payment.move_id.line_ids.filtered(
            lambda line: line.account_id == invoice_line[:1].account_id
        )
        (invoice_line[:1] | payment_line[:1]).reconcile()
        return payment
