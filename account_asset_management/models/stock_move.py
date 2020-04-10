# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")

    def _is_out(self):
        if not self.asset_id:
            return super(StockMove, self)._is_out()
        return False

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['asset_id'] = self.sale_line_id.asset_id.id
        if self.sale_line_id.asset_id:
            vals['asset_id'] = self.sale_line_id.asset_id.id,
        return vals
