# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields
from odoo.tests import Form, common


class TestAccountMove(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_tax = cls.env["account.tax"].create(
            {"name": "0%", "amount_type": "fixed", "type_tax_use": "sale", "amount": 0}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner test"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "list_price": 10,
                "taxes_id": [(6, 0, [cls.account_tax.id])],
            }
        )
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST",
                "user_type_id": cls.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )
        cls.other_account = cls.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "ACC",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_other_income"
                ).id,
                "reconcile": True,
            }
        )
        cls.env["account.journal"].create(
            {"name": "Test sale journal", "type": "sale", "code": "TEST-SALE"}
        )
        cls.journal_bank = cls.env["account.journal"].create(
            {"name": "Test bank journal", "type": "bank", "code": "TEST-BANK"}
        )

    def _create_invoice(self):
        move_form = Form(
            self.env["account.move"].with_context(default_type="out_invoice")
        )
        move_form.partner_id = self.partner
        move_form.invoice_date = fields.Date.from_string("2000-01-01")
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
        invoice = move_form.save()
        return invoice

    def test_invoice_move_update(self):
        invoice = self._create_invoice()
        invoice.line_ids.write({"date_maturity": False})
        invoice.write({"date": "1999-12-31"})
        invoice_line = invoice.line_ids.filtered(
            lambda x: x.account_id.internal_type == "receivable"
        )
        self.assertEqual(
            invoice_line.date_maturity, fields.Date.from_string("1999-12-31")
        )

    def test_invoice_reconciliation(self):
        invoice = self._create_invoice()
        invoice.action_post()
        invoice_line = invoice.line_ids.filtered(
            lambda x: x.account_id.internal_type == "receivable"
        )
        statement = self.env["account.bank.statement"].create(
            {
                "journal_id": self.journal_bank.id,
                "name": "Test",
                "date": "2000-01-01",
                "balance_end_real": 10.0,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "date": "2000-01-01",
                            "partner_id": self.partner.id,
                            "name": invoice.name,
                            "amount": 10.0,
                        },
                    )
                ],
            }
        )
        statement_line = statement.line_ids.filtered(lambda x: x.name == invoice.name)
        statement_line.process_reconciliation(
            counterpart_aml_dicts=[
                {
                    "move_line": invoice_line,
                    "credit": 10.0,
                    "debit": 0.0,
                    "name": invoice.name,
                }
            ]
        )
        self.assertEqual(invoice.invoice_payment_state, "paid")
        line_receivable = statement_line.journal_entry_ids.filtered(
            lambda x: x.account_id.internal_type == "receivable"
        )
        self.assertEqual(line_receivable.date_maturity, line_receivable.move_id.date)
