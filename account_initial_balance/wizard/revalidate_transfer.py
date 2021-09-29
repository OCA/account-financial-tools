# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
import time
from datetime import datetime, timedelta


class WizardRebookingPickingTransfer(models.TransientModel):
    _name = "wizard.rebooking.inventory"

    future_initial_balance = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company',
                                 string="Company",
                                 default=lambda self: self.env['res.company']._company_default_get('stock.inventory'))

    @api.multi
    def rebooking_inventory(self):
        context = dict(self._context or {})
        inventory = False
        if context.get('active_ids'):
            inventory = self.env['stock.inventory'].browse(context["active_ids"])
        if inventory:
            for line in inventory:
                line.future_initial_balance = True
            cron = self.env.ref('account_initial_balance.ir_cron_rebuild_inventory_scheduler')
            cron.write({'nextcall': (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:00')})
        return {'type': 'ir.actions.act_window_close'}
