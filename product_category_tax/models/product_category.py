# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    taxes_id = fields.Many2many(
        "account.tax",
        "product_category_taxes_rel",
        "categ_id",
        "tax_id",
        help="Default taxes used when selling the product.",
        string="Customer Taxes",
        domain=[("type_tax_use", "=", "sale")],
        default=lambda self: self.env.company.account_sale_tax_id,
    )
    supplier_taxes_id = fields.Many2many(
        "account.tax",
        "product_category_supplier_taxes_rel",
        "categ_id",
        "tax_id",
        string="Vendor Taxes",
        help="Default taxes used when buying the product.",
        domain=[("type_tax_use", "=", "purchase")],
        default=lambda self: self.env.company.account_purchase_tax_id,
    )

    def update_product_taxes(self):
        products = self.env["product.template"].search(
            [
                ("categ_id", "in", self.ids),
                ("taxes_updeatable_from_category", "=", True),
            ]
        )
        if not products:
            return True
        return products.set_tax_from_category()
