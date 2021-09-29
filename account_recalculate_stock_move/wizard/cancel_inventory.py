# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
import time


class WizardStockInventoryCancel(models.TransientModel):
    _name = "wizard.stock.inventory.cancel"

    date = fields.Date(required=True, default=fields.Date.context_today)
    remove_after = fields.Boolean()

    @api.multi
    def action_cancel(self):
        context = dict(self._context or {})
        inventory = self.env['stock.inventory'].browse(context["active_ids"])
        if not inventory:
            inventory = self.env['stock.inventory'].search([('date', '<=', self.date)])
        else:
            inventory = inventory.filtered(lambda r: r.date <= self.date)
        inventory.action_cancel_and_delete(self.remove_after)
        return {'type': 'ir.actions.act_window_close'}
