# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

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
                    "taxes_id": [(6, 0, categ.sudo().taxes_id.ids)],
                    "supplier_taxes_id": [(6, 0, categ.sudo().supplier_taxes_id.ids)],
                }
            )
        return True

    @api.model
    def _prepare_taxes_from_category(self, vals):
        existing_taxes = supplier_existing_taxes = set()
        categ = self.env["product.category"].browse(vals["categ_id"])
        if "taxes_id" in vals:
            existing_taxes = set(vals["taxes_id"][0][2])
        taxes = existing_taxes | set(categ.sudo().taxes_id.ids)
        vals["taxes_id"] = [(6, 0, taxes)]
        if "supplier_taxes_id" in vals:
            supplier_existing_taxes = set(vals["supplier_taxes_id"][0][2])
        supplier_taxes = supplier_existing_taxes | set(
            categ.sudo().supplier_taxes_id.ids
        )
        vals["supplier_taxes_id"] = [(6, 0, supplier_taxes)]
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("categ_id"):
                vals = self._prepare_taxes_from_category(vals)
        return super().create(vals_list)
