# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def _get_inventory_lines_values(self):
        vals =  super(Inventory, self)._get_inventory_lines_values()
        # _logger.info("INVENTORY VALS %s" % vals)
        # vals_new = []
        for line in vals:
            # vals_new.append(line.copy())
            product = self.env['product.product'].browse(line['product_id'])
            # _logger.info("PRODUCT INVENTORY %s(%s)" % (product.account_asset_ids.ids, line))
            # lot = self.env['stock.production.lot'].browse(line['prod_lot_id'])
            if not len(product.account_asset_ids.ids) > 0:
                price_subtotal_signed = product.standard_price
                # Check in product valuations
                product_tmpl = product.product_tmpl_id.categ_id
                if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.asset_profile_id:
                    line['asset_profile_id'] = product_tmpl.property_stock_valuation_account_id.asset_profile_id.id
                    if product_tmpl.property_stock_valuation_account_id.asset_profile_id.threshold >= price_subtotal_signed:
                        line['asset_profile_id'] = product_tmpl.property_stock_valuation_account_id.asset_profile_id.threshold_profile_id.id

                if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.tax_profile_id:
                    line['tax_profile_id'] = product_tmpl.property_stock_valuation_account_id.tax_profile_id.id
                    if product_tmpl.property_stock_valuation_account_id.tax_profile_id.threshold >= price_subtotal_signed:
                        line['tax_profile_id'] = product_tmpl.property_stock_valuation_account_id.tax_profile_id.threshold_tax_profile_id.id
            elif line.get('prod_lot_id'):
                assets = product.account_asset_ids.filtered(lambda r: r.lot_id.id == line['prod_lot_id'])
                if assets:
                    line['asset_id'] = assets[0].id
                # if len(assets.ids) >= 1 and line['theoretical_qty'] >= 1:
                #     qty = 0
                #     if len(assets.ids) < line['theoretical_qty']:
                #         vals_new[-1]['theoretical_qty'] = line['theoretical_qty'] - len(assets.ids)
                #         qty = vals_new[-1]['theoretical_qty']
                #     elif len(assets.ids) > line['theoretical_qty']:
                #         assets = assets[:line['theoretical_qty']]
                #     elif len(assets.ids) == 1 and line['theoretical_qty'] == 1:
                #         vals_new[-1]['asset_id'] = assets[0].id
                #         continue
                #     for asset in assets:
                #         qty += 1
                #         if qty > 1:
                #             vals_new.append(line.copy())
                #         vals_new[-1]['asset_id'] = asset.id
                #         vals_new[-1]['theoretical_qty'] = 1
                    # if qty < line['theoretical_qty']:
                    #     vals_new[-1]['theoretical_qty'] = line['theoretical_qty'] - qty
                    #     vals_new[-1]['prod_lot_id'] = False
        return vals


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")
    asset_profile_id = fields.Many2one(
        comodel_name='account.asset.profile',
        string='Asset Profile')
    tax_profile_id = fields.Many2one(
        comodel_name='account.bg.asset.profile',
        string='Tax Asset Profile')
    account_asset_ids = fields.One2many("account.asset", related="product_id.account_asset_ids")

    @api.onchange('product_id')
    def onchange_product(self):
        res = super(InventoryLine, self).onchange_product()
        if self.product_id:
            if not len(self.account_asset_ids.ids) > 0:
                price_subtotal_signed = self.standard_price
                # Check in product valuations
                product_tmpl = self.product_id.product_tmpl_id.categ_id
                if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.asset_profile_id:
                    self.asset_profile_id = product_tmpl.property_stock_valuation_account_id.asset_profile_id
                    if product_tmpl.property_stock_valuation_account_id.asset_profile_id.threshold >= price_subtotal_signed:
                        self.asset_profile_id = product_tmpl.property_stock_valuation_account_id.asset_profile_id.threshold_profile_id

                if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.tax_profile_id:
                    self.tax_profile_id = product_tmpl.property_stock_valuation_account_id.tax_profile_id
                    if product_tmpl.property_stock_valuation_account_id.tax_profile_id.threshold >= price_subtotal_signed:
                        self.tax_profile_id = product_tmpl.property_stock_valuation_account_id.tax_profile_id.threshold_tax_profile_id
        return res

    # @api.onchange('prod_lot_id')
    # def onchange_prod_lot_id(self):
    #     res = {}
    #     if self.prod_lot_id:
    #         assets = self.product_id.account_asset_ids.filtered(lambda r: r.lot_id == self.prod_lot_id)
    #         if assets:
    #             ids = assets.ids
    #             res['domain'] = {'asset_id', [('id', 'in', ids)]}
    #     return res

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super()._get_move_values(qty, location_id, location_dest_id, out)
        if self.asset_id:
            res['move_line_ids'][0][2].update({'asset_id': self.asset_id.id})
        if self.asset_profile_id and qty == 1 and not out:
            # make asset
            res.update({'asset_profile_id': self.asset_profile_id.id})
            res.update({'tax_profile_id': self.tax_profile_id.id})
            res['name'] = "%s%s - %s" % (self.prod_lot_id and "(%s)/" % self.prod_lot_id.name or "",
                                         self.product_id.display_name,
                                         res['name'])
        return res
