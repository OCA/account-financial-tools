# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    equipment_ids = fields.Many2many(
        comodel_name="maintenance.equipment", string="Equipments",
    )
    equipment_count = fields.Integer(
        string="Equipment count", compute="_compute_equipment_count",
    )

    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for asset in self:
            asset.equipment_count = len(asset.equipment_ids)

    @api.multi
    def button_open_equipment(self):
        self.ensure_one()
        res = self.env.ref('maintenance.hr_equipment_action').read()[0]
        res['domain'] = [('asset_ids', 'in', self.ids)]
        res['context'] = {'default_asset_ids': [(6, 0, self.ids)]}
        return res
