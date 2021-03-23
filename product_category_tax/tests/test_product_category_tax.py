# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common


class ProductCategoryTax(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.categ_obj = cls.env["product.category"]
        cls.product_obj = cls.env["product.product"]
        cls.tax_model = cls.env["account.tax"]

        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")

        # Create product and related records:
        cls.tax_sale = cls.tax_model.create(
            {
                "name": "Include tax",
                "type_tax_use": "sale",
                "amount": 21.00,
                "price_include": True,
            }
        )
        cls.tax_purchase = cls.tax_model.create(
            {
                "name": "Some tax",
                "type_tax_use": "purchase",
                "amount": 21.00,
                "price_include": True,
            }
        )
        cls.tax_purchase2 = cls.tax_model.create(
            {
                "name": "Abusive tax",
                "type_tax_use": "purchase",
                "amount": 50.00,
                "price_include": True,
            }
        )

    def test_01_copy_taxes(self):
        """ Default taxes taken from the category"""
        test_categ = self.categ_obj.create(
            {
                "name": "Super Category",
                "taxes_id": [(6, 0, self.tax_sale.ids)],
                "supplier_taxes_id": [(6, 0, self.tax_purchase.ids)],
            }
        )
        self.product_test = self.product_obj.create(
            {"name": "TEST 01", "categ_id": test_categ.id, "list_price": 155.0}
        )
        self.product_test.product_tmpl_id.onchange_categ_id()
        self.assertEqual(self.product_test.supplier_taxes_id, self.tax_purchase)

    def test_02_update_taxes(self):
        """ Default update """
        self.product_test = self.product_obj.create(
            {
                "name": "TEST 02",
                "default_code": "TESTcode2",
                "list_price": 155.0,
                "supplier_taxes_id": [(6, 0, self.tax_purchase2.ids)],
            }
        )
        test_categ = self.categ_obj.create(
            {
                "name": "Super Category",
                "taxes_id": [(6, 0, self.tax_sale.ids)],
                "supplier_taxes_id": [(6, 0, self.tax_purchase.ids)],
            }
        )
        self.assertEqual(self.product_test.supplier_taxes_id, self.tax_purchase2)
        self.product_test.categ_id = test_categ.id
        test_categ.update_product_taxes()
        self.assertEqual(self.product_test.supplier_taxes_id, self.tax_purchase)

    def test_03_taxes_not_updeatable(self):
        """ Avoid update specific products"""
        self.product_test3 = self.product_obj.create(
            {
                "name": "TEST 03",
                "default_code": "TESTcode3",
                "list_price": 155.0,
                "supplier_taxes_id": [(6, 0, self.tax_purchase2.ids)],
            }
        )
        self.product_test4 = self.product_obj.create(
            {
                "name": "TEST 04",
                "default_code": "TESTcode3",
                "list_price": 155.0,
                "taxes_updeatable_from_category": False,
                "supplier_taxes_id": [(6, 0, self.tax_purchase2.ids)],
            }
        )
        test_categ = self.categ_obj.create(
            {
                "name": "Super Category",
                "taxes_id": [(6, 0, self.tax_sale.ids)],
                "supplier_taxes_id": [(6, 0, self.tax_purchase.ids)],
            }
        )
        self.product_test3.categ_id = test_categ.id
        self.product_test4.categ_id = test_categ.id
        test_categ.update_product_taxes()
        self.assertEqual(self.product_test3.supplier_taxes_id, self.tax_purchase)
        self.assertNotEqual(self.product_test4.supplier_taxes_id, self.tax_purchase)
