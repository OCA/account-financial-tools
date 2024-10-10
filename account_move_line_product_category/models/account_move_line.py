# Copyright 2018 Jacques-Etienne Baudoux (BCIM sprl) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    categ_id = fields.Many2one(
        comodel_name="product.category",
        string="Product Category",
        index="btree_not_null",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("product_id") and "categ_id" not in vals:
                product = self.env["product.product"].browse(vals["product_id"])
                vals["categ_id"] = product.categ_id.id
        return super().create(vals_list)

    def write(self, vals):
        if "product_id" in vals and "categ_id" not in vals:
            if vals.get("product_id"):
                product = self.env["product.product"].browse(vals["product_id"])
                vals["categ_id"] = product.categ_id.id
            else:
                vals["categ_id"] = False
        return super().write(vals)
