# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("categ_id")
    def onchange_categ_id(self):
        if self.categ_id:
            self.set_tax_from_category()

    def set_tax_from_category(self):
        self.ensure_one()
        self.taxes_id = [(6, 0, self.categ_id.taxes_id.ids)]
        self.supplier_taxes_id = [(6, 0, self.categ_id.supplier_taxes_id.ids)]
