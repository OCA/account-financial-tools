# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _


class WizardRebuildMoveStockInventory(models.TransientModel):
    _name = "wizard.rebuild.move.stock.inventory"

    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 default=lambda self: self.env.user.company_id.id)

    @api.multi
    def rebuild_stock_inventory(self):
        context = dict(self._context or {})
        inventories = False
        if context.get('active_ids'):
            inventories = self.env['stock.inventory'].browse(context["active_ids"])
        if not inventories:
            if self.company_id:
                domain = [('company_id', '=', self.company_id.id)]
            inventories = self.env['stock.inventory'].search(domain)
        for inventory in inventories:
            inventory.with_context(self._context, rebuld_try=True).rebuild_account_move()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def server_rebuild_action(self):
        for record in self:
            action = self.env.ref('account_recalculate_stock_move.action_recalculate_inventory')
            action.with_context(self._context, company_id=self.env.user.company_id.id, rebuld_try=True).run()
            # _logger.info("ACTION %s" % action)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def server_rebuild(self):
        if self._context.get('active_ids'):
            company_id = self._context.get('company_id') or self.env.user.company_id.id
            inventory = self.env['stock.inventory'].browse(self._context["active_ids"])
            inventory = inventory.filtered(lambda r: r.company_id == company_id)
            inventory.rebuild_account_move()
