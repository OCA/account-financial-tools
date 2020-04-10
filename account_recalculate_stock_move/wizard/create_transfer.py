# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
import time


class WizardRebookingMoveTransfer(models.TransientModel):
    _name = "wizard.rebooking.move.transfer"

    date = fields.Date(required=True, default=fields.Date.context_today)

    @api.multi
    def rebooking_create_move(self):
        context = dict(self._context or {})
        stock = self.env['stock.move'].browse(context["active_ids"])
        stock.with_context(dict(self._context, force_accounting_date=self.date)).with_context(dict(self.env.context, rebuld_try=True))._rebuild_account_move()
        return {'type': 'ir.actions.act_window_close'}
