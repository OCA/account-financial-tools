# Copyright 2024 ForgeFlow SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountInvoiceAnalysisCountryGroup(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.expenses_account = cls.env["account.account"].create(
            {
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.partner.country_id = cls.env.ref("base.ar")
        cls.south_america = cls.env.ref("base.south_america")

        # Invoice created with tests Form
        cls.invoice1 = cls.init_invoice("in_invoice")

        # Invoice created with standard create
        cls.invoice2 = cls.env["account.move"].create(
            {
                "partner_id": cls.partner.id,
                "move_type": "in_invoice",
            }
        )

        cls.invoice2.invoice_line_ids += cls.env["account.move.line"].new(
            {
                "product_id": cls.env.ref("product.product_product_4").id,
                "quantity": 1.0,
                "price_unit": 100.0,
                "name": "cool product",
            }
        )

    def test_01_check_lines(self):
        """Check country group from the partner is taken"""
        self.assertFalse(
            self.invoice1.invoice_line_ids.country_group_id,
            "Default cost center per line not set",
        )

        self.assertEqual(
            self.invoice2.invoice_line_ids[0].country_group_id, self.south_america
        )
