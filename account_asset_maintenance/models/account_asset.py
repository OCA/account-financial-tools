# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')

    @api.model
    def _check_internal_call(self, equipment):
        if not self._context.get('internal_call', False) and equipment:
            return True
        return False

    @api.model
    def create(self, values):
        context = self.env.context.copy()
        inv_types = ['in_invoice', 'in_refund', 'out_invoice', 'out_refund']
        if context.get('default_type', False) in inv_types:
            context.pop('default_type')
        res = super(AccountAsset, self.with_context(context)).create(values)
        if self._check_internal_call(res.equipment_id):
            ctx = dict(context, internal_call=True)
            res.equipment_id.with_context(ctx).write({'asset_id': res.id})
        return res

    @api.multi
    def write(self, values):
        for asset in self:
            ctx = dict(self.env.context, internal_call=True)
            if self._check_internal_call(asset.equipment_id):
                asset.equipment_id.with_context(ctx).write({'asset_id': None})
            super(AccountAsset, asset).write(values)
            if self._check_internal_call(asset.equipment_id):
                asset.equipment_id.with_context(ctx).write(
                    {'asset_id': asset.id}
                )
        return True
