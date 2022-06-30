# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("categ_id")
    def _onchange_categ_id_set_taxes(self):
        if self.categ_id:
            self.set_tax_from_category()

    def set_tax_from_category(self):
        return self.product_tmpl_id.set_tax_from_category()
