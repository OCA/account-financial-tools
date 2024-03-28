# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    taxes_updeatable_from_category = fields.Boolean(default=True)

    @api.onchange("categ_id")
    def _onchange_categ_id_set_taxes(self):
        if self.categ_id:
            self.taxes_id = [(6, 0, self.categ_id.taxes_id.ids)]
            self.supplier_taxes_id = [(6, 0, self.categ_id.supplier_taxes_id.ids)]

    def set_tax_from_category(self):
        records_by_categ = defaultdict(lambda: self.browse())
        for rec in self:
            records_by_categ[rec.categ_id] += rec
        for categ, records in records_by_categ.items():
            records.write(
                {
                    "taxes_id": [(6, 0, categ.taxes_id.ids)],
                    "supplier_taxes_id": [(6, 0, categ.supplier_taxes_id.ids)],
                }
            )
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("categ_id"):
                if "taxes_id" not in vals:
                    categ = self.env["product.category"].browse(vals["categ_id"])
                    vals["taxes_id"] = [(6, 0, categ.taxes_id.ids)]
                if "supplier_taxes_id" not in vals:
                    categ = self.env["product.category"].browse(vals["categ_id"])
                    vals["supplier_taxes_id"] = [(6, 0, categ.supplier_taxes_id.ids)]
        return super().create(vals_list)
