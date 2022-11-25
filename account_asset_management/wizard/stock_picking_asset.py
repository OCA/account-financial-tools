# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class StockPickingAsset(models.TransientModel):
    _name = 'stock.picking.asset'
    _description = 'Wizard to assets in stock picking lines'

    picking_id = fields.Many2one('stock.picking', 'Wizard stock picking asset')
    asset_lines = fields.One2many('stock.picking.asset.lines', 'picking_asset_id', 'Picking Asset lines')

    # def default_get(self, fields_list):
    #     res = super(StockPickingAsset, self).default_get(fields_list)
    #     if not res:
    #         res = {}
    #     pickings = False
    #     if self._context.get('active_id'):
    #         pickings = self.env['stock.picking'].browse([self._context['active_id']])
    #
    #     if pickings:
    #         line_obj = self.env['stock.picking.asset.lines']
    #         for picking in pickings:
    #             lines = []
    #             for line in picking.move_line_ids:
    #                 asset_profile = line.move_id._check_for_assets()
    #                 if asset_profile:
    #                     line_obj = line_obj.new({
    #                         'move_id': line.move_id.id,
    #                         'move_line_id': line.id,
    #                         'product_id': line.product_id.id,
    #                         'asset_profile_id': asset_profile.get(line) and asset_profile[line][
    #                             'asset_profile_id'].id or False,
    #                         'tax_asset_profile_id': asset_profile.get(line) and asset_profile[line][
    #                             'tax_profile_id'].id or False,
    #                         'quantity': line.qty_done,
    #                         'uom_id': line.product_uom_id.id,
    #                         'price_unit': line.move_id.price_unit,
    #                     })
    #                     lines.append((0, False, line_obj._convert_to_write(line_obj._cache)))
    #             res.update({
    #                 'picking_id': picking.id,
    #                 'asset_lines': lines,
    #             })
    #     return res

    @api.multi
    def rebuild_picking_move(self):
        asset_obj = self.env['account.asset']
        for record in self:
            picking = record.picking_id
            lines = []
            for line in picking.move_lines.mapped('move_line_ids'):
                move = line.move_id
                if move._is_out():
                    for asset_line in record.asset_lines.filtered(lambda r: r.move_line_id == line):
                        asset_found = asset_obj.search([('product_id', '=', asset_line.product_id.id),
                                                        ('lot_id', '=', asset_line.lot_id.id)],
                                                       limit=1)
                        if asset_found:
                            line.write({
                                'asset_id': asset_found.id,
                            })
                            if len(move.account_move_ids.ids) > 0:
                                lines.append(line.id)
                elif move._is_in():
                    for asset_line in record.asset_lines.\
                            filtered(lambda r: r.move_line_id == line and not r.move_id.asset_profile_id):

                        move.write({
                            'asset_profile_id': asset_line.asset_profile_id.id,
                            'tax_profile_id':
                                asset_line.tax_asset_profile_id and asset_line.tax_asset_profile_id.id or False,
                        })
                        # _logger.info("ASSET RE-TYPE %s" % move.asset_profile_id)
                    if len(move.account_move_ids.ids) > 0:
                        lines.append(line.id)
            if lines:
                picking.rebuild_account_move()
        return True


class StockPickingAssetLines(models.TransientModel):
    _name = 'stock.picking.asset.lines'
    _description = 'Wizard to assets in stock picking lines'

    picking_asset_id = fields.Many2one('stock.picking.asset', 'Wizard stock picking asset')
    move_line_id = fields.Many2one('stock.move.line', 'Stock move line')
    move_id = fields.Many2one('stock.move', 'Stock move line')
    product_id = fields.Many2one('product.product', 'Product', related='move_line_id.product_id', store=True)
    asset_profile_id = fields.Many2one('account.asset.profile', 'Asset profile')
    tax_asset_profile_id = fields.Many2one('account.bg.asset.profile', 'Tax asset profile')
    quantity = fields.Float('Quantity', related='move_line_id.qty_done')
    uom_id = fields.Many2one('product.uom', 'UOM', related='move_line_id.product_uom_id')
    price_unit = fields.Float('Unit price', related='move_id.price_unit')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    lot_name = fields.Char('Lot/Serial Number')
