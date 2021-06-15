# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class Picking(models.Model):
    _inherit = "stock.picking"

    count_assets = fields.Integer('Count assets', compute='_compute_count_assets')

    @api.multi
    def _compute_count_assets(self):
        for record in self:
            record.count_assets = len(record.move_lines._check_for_assets())

    @api.multi
    def action_asset_ids(self):
        assets = []
        line_obj = self.env['stock.picking.asset.lines']
        for picking in self:
            lines = []
            for line in picking.move_line_ids:
                asset_profile = line.move_id._check_for_assets()
                if asset_profile:
                    line_obj = line_obj.new({
                        'move_id': line.move_id.id,
                        'move_line_id': line.id,
                        'product_id': line.product_id.id,
                        'asset_profile_id': asset_profile.get(line) and asset_profile[line]['asset_profile_id'].id or False,
                        'tax_asset_profile_id': asset_profile.get(line) and asset_profile[line]['tax_profile_id'].id or False,
                        'quantity': line.qty_done,
                        'uom_id': line.product_uom_id.id,
                        'price_unit': line.move_id.price_unit,
                    })
                    lines.append((0, False, line_obj._convert_to_write(line_obj._cache)))
            asset = self.env['stock.picking.asset'].create({
                'picking_id': picking.id,
                'asset_lines': lines,
            })
            assets += asset.asset_lines.ids
        action = self.env.ref('account_asset_management.account_stock_picking_asset_lines').read()[0]
        if len(assets) > 1:
            action['domain'] = [('id', 'in', assets)]
        elif len(assets) == 1:
            action['views'] = [(self.env.ref('account_asset_management.stock_picking_asset_lines_view_form').id, 'form')]
            action['res_id'] = assets[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class StockPickingAsset(models.TransientModel):
    _name = 'stock.picking.asset'
    _description = 'Wizard to assets in stock picking lines'

    picking_id = fields.Many2one('stock.picking', 'Wizard stock picking asset')
    asset_lines = fields.One2many('stock.picking.asset.lines', 'picking_asset_id', 'Picking Asset lines')

    def default_get(self, fields_list):
        res = super(StockPickingAsset, self).default_get(fields_list)
        if not res:
            res = {}
        pickings = False
        if self._context.get('active_id'):
            pickings = self.env['stock.picking'].browse([self._context['active_id']])

        if pickings:
            line_obj = self.env['stock.picking.asset.lines']
            for picking in pickings:
                lines = []
                for line in picking.move_line_ids:
                    asset_profile = line.move_id._check_for_assets()
                    if asset_profile:
                        line_obj = line_obj.new({
                            'move_id': line.move_id.id,
                            'move_line_id': line.id,
                            'product_id': line.product_id.id,
                            'asset_profile_id': asset_profile.get(line) and asset_profile[line][
                                'asset_profile_id'].id or False,
                            'tax_asset_profile_id': asset_profile.get(line) and asset_profile[line][
                                'tax_profile_id'].id or False,
                            'quantity': line.qty_done,
                            'uom_id': line.product_uom_id.id,
                            'price_unit': line.move_id.price_unit,
                        })
                        lines.append((0, False, line_obj._convert_to_write(line_obj._cache)))
                res.update({
                    'picking_id': picking.id,
                    'asset_lines': lines,
                })
        return res


class StockPickingAssetLines(models.TransientModel):
    _name = 'stock.picking.asset.lines'
    _description = 'Wizard to assets in stock picking lines'

    picking_asset_id = fields.Many2one('stock.picking.asset', 'Wizard stock picking asset')
    move_line_id = fields.Many2one('stock.move.line', 'Stock move line')
    move_id = fields.Many2one('stock.move', 'Stock move line')
    product_id = fields.Many2one('product.product', 'Product', related='move_line_id.product_id', store=True)
    asset_profile_id = fields.Many2one('account.asset.profile', 'Asset profile', related='move_id.asset_profile_id', store=True)
    tax_asset_profile_id = fields.Many2one('account.bg.asset.profile', 'Tax asset profile', related="move_id.tax_profile_id", store=True)
    quantity = fields.Float('Quantity', related='move_line_id.qty_done')
    uom_id = fields.Many2one('product.uom', 'UOM', related='move_line_id.product_uom_id')
    price_unit = fields.Float('Unit price', related='move_id.price_unit')

