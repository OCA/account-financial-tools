# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    count_assets = fields.Integer('Count assets', compute='_compute_count_assets')
    count_in_assets = fields.Integer('Count added assets', compute='_compute_count_assets')

    @api.multi
    def _compute_count_assets(self):
        for record in self:
            record.count_assets = len(record.move_lines._check_for_assets())
            record.count_in_assets = len([x for x in record.mapped('move_lines').mapped('move_line_ids') if x.asset_id])

    @api.multi
    def action_asset_ids(self):
        assets = []
        line_obj = self.env['stock.picking.asset.lines']
        for picking in self:
            lines = []
            for line in picking.move_line_ids:
                # _logger.info("PICKING %s:%s" % (picking, line))
                asset_profile = line.move_id._check_for_assets()
                # _logger.info("ASSET PROFILE %s" % asset_profile)
                if asset_profile and asset_profile.get(line.move_id):
                    get_asset_profile = asset_profile.get(line.move_id)
                    pull_asset_profile_id = pull_tax_profile_id = False
                    if get_asset_profile and get_asset_profile.get('asset_profile_id'):
                        pull_asset_profile_id = get_asset_profile['asset_profile_id'].id
                    if get_asset_profile and get_asset_profile.get('tax_profile_id'):
                        pull_tax_profile_id = get_asset_profile['tax_profile_id'].id
                    line_obj = line_obj.new({
                        'move_id': line.move_id.id,
                        'move_line_id': line.id,
                        'product_id': line.product_id.id,
                        'asset_profile_id': pull_asset_profile_id,
                        'tax_asset_profile_id': pull_tax_profile_id,
                        'quantity': line.qty_done,
                        'uom_id': line.product_uom_id.id,
                        'price_unit': line.move_id.price_unit,
                        'lot_id': line.lot_id.id,
                        'lot_name': line.lot_name,
                    })
                    lines.append((0, False, line_obj._convert_to_write(line_obj._cache)))
            # _logger.info("PICKING LINES %s" % lines)
            asset = self.env['stock.picking.asset'].create({
                'picking_id': picking.id,
                'asset_lines': lines,
            })
            assets += asset.ids
            if not assets:
                return {'type': 'ir.actions.act_window_close'}
            return {
                'name': _("Generate Asset From Picking"),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.picking.asset',
                'target': 'new',
                'type': 'ir.actions.act_window',
                'res_id': assets[0]
            }

    @api.multi
    def action_view_asset(self):
        assets = []
        action = self.env.ref('account_asset_management.account_asset_action').read()[0]
        for record in self:
            if record.move_lines:
                for line in record.move_lines.mapped('move_line_ids'):
                    assets.append(line.asset_id.id)
        if not assets:
            action = {'type': 'ir.actions.act_window_close'}
        elif len(assets) == 1:
            action['views'] = [(self.env.ref('account_asset_management.account_asset_view_form').id, 'form')]
            action['res_id'] = assets[0]
        elif len(assets) > 1:
            action['domain'] = [('id', 'in', assets)]
        return action
