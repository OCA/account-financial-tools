# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from statistics import mean

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    account_asset_ids = fields.One2many("account.asset", compute="_compute_account_asset_ids", string="Asset files")
    product_asset_ids = fields.Many2many("account.asset", relation="asset_product_tmpl_rel", column1="product_tmpl_id", column2="asset_id", string="Linked to asset")

    @api.multi
    def _compute_account_asset_ids(self):
        for template in self:
            if len(template.product_variant_ids) > 0:
                template.account_asset_ids = template.product_variant_ids.mapped("account_asset_ids")
            else:
                template.account_asset_ids = False


class ProductProduct(models.Model):
    _inherit = "product.product"

    account_asset_ids = fields.One2many("account.asset", "product_id", string="Asset files")
    value_depreciated = fields.Float(compute='_compute_value_depreciated')

    @api.multi
    def _compute_value_depreciated(self):
        for product in self:
            if len(product.account_asset_ids.ids) > 0:
                product.value_depreciated = mean([x.value_depreciated for x in product.account_asset_ids if x.type == 'normal'])
            else:
                product.value_depreciated = 0.0
