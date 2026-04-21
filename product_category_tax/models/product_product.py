# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import Command, api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("categ_id")
    def _onchange_categ_id_set_taxes(self):
        if self.categ_id:
            self.set_tax_from_category()

    def set_tax_from_category(self):
        return self.product_tmpl_id.set_tax_from_category()

    @api.model_create_multi
    def create(self, vals_list):
        categ_ids = [v["categ_id"] for v in vals_list if v.get("categ_id")]
        if categ_ids:
            categs = self.env["product.category"].browse(categ_ids)
            categs.mapped("taxes_id")
            categs.mapped("supplier_taxes_id")
            categ_map = {c.id: c for c in categs}
            for vals in vals_list:
                categ_id = vals.get("categ_id")
                if categ_id:
                    categ = categ_map[categ_id]
                    if "taxes_id" not in vals:
                        vals["taxes_id"] = [Command.set(categ.taxes_id.ids)]
                    if "supplier_taxes_id" not in vals:
                        vals["supplier_taxes_id"] = [
                            Command.set(categ.supplier_taxes_id.ids)
                        ]
        return super().create(vals_list)
