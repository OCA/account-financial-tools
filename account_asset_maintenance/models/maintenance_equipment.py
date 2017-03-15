# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class MaintenanceEquipment(models.Model):

    _inherit = 'maintenance.equipment'

    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    equipment_scrap_template_id = fields.Many2one(
        'mail.template',
        string='Equipment Scrap Email Template',
        default=(lambda self:
                 self.env.user.company_id.equipment_scrap_template_id)
    )

    @api.multi
    def action_perform_scrap(self):
        self.ensure_one()
        action = self.env.ref(
            'account_asset_maintenance.wizard_perform_equipment_scrap_action')
        result = action.read()[0]
        return result

    @api.model
    def create(self, values):
        res = super(MaintenanceEquipment, self).create(values)
        if not self._context.get('internal_call', False) and res.asset_id:
            ctx = dict(self.env.context, internal_call=True)
            res.asset_id.with_context(ctx).write({'equipment_id': res.id})
        return res

    @api.multi
    def write(self, values):
        for equip in self:
            ctx = dict(self.env.context, internal_call=True)
            if not self._context.get(
                    'internal_call',
                    False) and 'asset_id' in values:
                equip.asset_id.with_context(ctx).write({'equipment_id': None})
            super(MaintenanceEquipment, equip).write(values)
            if not self._context.get(
                    'internal_call',
                    False) and 'asset_id' in values:
                equip.asset_id.with_context(ctx).write(
                    {'equipment_id': equip.id})
        return True
