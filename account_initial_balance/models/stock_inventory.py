# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Inventory(models.Model):
    _inherit = "stock.inventory"

    is_initial_balance = fields.Boolean('This is initial balance')


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super()._get_move_values(qty, location_id, location_dest_id, out)
        res['is_initial_balance'] = self.inventory_id.is_initial_balance
        return res
