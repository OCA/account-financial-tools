# Copyright 2021 CreuBlanca


from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountFiscalPositionVatCheck(TransactionCase):
    def setUp(self):

        super().setUp()

        self.customer = self.env["res.partner"].create(
            {"name": "Test customer", "customer_rank": 1, "vat": False}
        )

        self.fiscal_position_vat_required = self.env["account.fiscal.position"].create(
            {"name": "Test Fiscal Position Vat Required", "vat_required": True}
        )
        self.fiscal_position_no_vat_required = self.env[
            "account.fiscal.position"
        ].create(
            {"name": "Test Fiscal Position No Vat Required", "vat_required": False}
        )

        product = self.browse_ref("product.product_product_5")
        main_company = self.env.ref("base.main_company")
        account = self.env["account.account"].create(
            {
                "company_id": main_company.id,
                "name": "Testing Product account",
                "code": "test_product",
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
            }
        )
        self.invoice = self.env["account.move"].create(
            {"partner_id": self.customer.id, "type": "out_invoice"}
        )
        self.env["account.move.line"].create(
            {
                "move_id": self.invoice.id,
                "product_id": product.id,
                "quantity": 1,
                "account_id": account.id,
                "name": "Test product",
            }
        )
        self.invoice._onchange_invoice_line_ids()

    def test_warning_res_partner(self):

        # Vat required with not customer vat set
        self.customer.property_account_position_id = self.fiscal_position_vat_required
        res = self.customer.fiscal_position_change()
        self.assertTrue(res)

        # Vat not required
        self.customer.property_account_position_id = (
            self.fiscal_position_no_vat_required
        )
        res = self.customer.fiscal_position_change()
        self.assertFalse(res)

        # Vat required with customer vat set
        self.customer.vat = "1234"
        self.customer.property_account_position_id = self.fiscal_position_vat_required
        res = self.customer.fiscal_position_change()
        self.assertFalse(res)

    def test_warning_account_invoice_vat_required(self):

        # Customer without vat set
        self.customer.property_account_position_id = self.fiscal_position_vat_required
        self.invoice.fiscal_position_id = self.fiscal_position_vat_required
        with self.assertRaises(UserError):
            self.invoice.post()
        self.assertNotEqual(self.invoice.state, "posted")

        # Customer with vat set
        self.customer.vat = "1234"
        self.invoice.post()
        self.assertEqual(self.invoice.state, "posted")

    def test_warning_account_invoice_vat_not_required(self):
        self.customer.property_account_position_id = self.fiscal_position_vat_required
        self.assertFalse(self.customer.vat)
        self.invoice.fiscal_position_id = self.fiscal_position_no_vat_required
        self.invoice.post()
        self.assertEqual(self.invoice.state, "posted")
