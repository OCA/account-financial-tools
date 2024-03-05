# Copyright 2022 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields
from odoo.tests.common import Form, TransactionCase


class TestProductAccountCreditNote(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Company
        cls.company = cls.env.ref("base.main_company")
        cls.journal_model = cls.env["account.journal"]
        cls.journal = cls.journal_model.create(
            {
                "name": "Test journal",
                "type": "sale",
                "code": "test-sale-journal",
                "company_id": cls.company.id,
            }
        )
        cls.property_account_receivable_id = cls.env["account.account"].create(
            {
                "name": "Test Payable Account",
                "code": "test_payable",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
                "reconcile": True,
            }
        )
        # Partner
        cls.partner_1 = (
            cls.env["res.partner"]
            .with_company(cls.company.id)
            .create(
                {
                    "name": "Test Partner",
                    "customer_rank": 1,
                    "property_account_receivable_id": cls.property_account_receivable_id.id,
                }
            )
        )

        # Account
        cls.income_account = cls.env["account.account"].create(
            {
                "name": "Test Income Account",
                "code": "test_income",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
            }
        )
        cls.credit_note_account = cls.env["account.account"].create(
            {
                "name": "Test Credit Note Account",
                "code": "test_credit_note",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
            }
        )
        # Product Category
        cls.product_category_no_credit_note = cls.env["product.category"].create(
            {
                "name": "Test Product Category - No Credit note",
                "property_account_income_categ_id": cls.income_account.id,
            }
        )
        cls.product_category_credit_note = cls.env["product.category"].create(
            {
                "name": "Test Product Category",
                "property_account_income_categ_id": cls.income_account.id,
                "credit_note_account_categ_id": cls.credit_note_account.id,
            }
        )
        # Product
        cls.product_no_credit_note = cls.env["product.product"].create(
            {
                "name": "Test",
                "standard_price": 500.0,
                "property_account_income_id": cls.income_account.id,
                "categ_id": cls.product_category_no_credit_note.id,
            }
        )
        cls.product_categ_credit_note = cls.env["product.product"].create(
            {
                "name": "Test",
                "standard_price": 500.0,
                "property_account_income_id": cls.income_account.id,
                "categ_id": cls.product_category_credit_note.id,
            }
        )
        cls.product_credit_note = cls.env["product.product"].create(
            {
                "name": "Test",
                "standard_price": 500.0,
                "property_account_income_id": cls.income_account.id,
                "credit_note_account_id": cls.credit_note_account.id,
            }
        )

    def _create_invoice(self, default_move_type, partner, product, line_account=None):
        move_form_invoice1 = Form(
            self.env["account.move"].with_context(
                default_move_type=default_move_type, default_journal_id=self.journal.id
            )
        )
        move_form_invoice1.partner_id = partner
        move_form_invoice1.invoice_date = fields.Date.today()
        move_form_invoice1.journal_id = self.journal
        with move_form_invoice1.invoice_line_ids.new() as line_form:
            line_form.product_id = product
            line_form.name = "product test cost 100"
            line_form.quantity = 1.0
            line_form.price_unit = 100.0
            # line_form.account_id = line_account
        return move_form_invoice1.save()

    def test_account_invoice_type(self):
        move_form_invoice1 = self._create_invoice(
            default_move_type="out_invoice",
            partner=self.partner_1,
            product=self.product_no_credit_note,
        )
        self.assertEqual(
            move_form_invoice1.invoice_line_ids.account_id, self.income_account
        )
        move_form_invoice2 = self._create_invoice(
            default_move_type="out_invoice",
            partner=self.partner_1,
            product=self.product_credit_note,
        )
        self.assertEqual(
            move_form_invoice2.invoice_line_ids.account_id, self.income_account
        )

    def test_account_refund_type(self):
        move_form_refund1 = self._create_invoice(
            default_move_type="out_refund",
            partner=self.partner_1,
            product=self.product_no_credit_note,
        )
        self.assertEqual(
            move_form_refund1.invoice_line_ids.account_id, self.income_account
        )
        move_form_refund2 = self._create_invoice(
            default_move_type="out_refund",
            partner=self.partner_1,
            product=self.product_credit_note,
        )
        self.assertEqual(
            move_form_refund2.invoice_line_ids.account_id, self.credit_note_account
        )
        move_form_refund3 = self._create_invoice(
            default_move_type="out_refund",
            partner=self.partner_1,
            product=self.product_categ_credit_note,
        )
        self.assertEqual(
            move_form_refund3.invoice_line_ids.account_id, self.credit_note_account
        )
