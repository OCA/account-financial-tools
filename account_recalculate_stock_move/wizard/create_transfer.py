# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
import time


class WizardRebookingMoveTransfer(models.TransientModel):
    _name = "wizard.rebooking.move.transfer"

    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date()
    only_remove = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company', string="Company")

    @api.multi
    def rebooking_create_move(self):
        context = dict(self._context or {})
        moves = False
        if context.get('active_ids'):
            moves = self.env['stock.move'].browse(context["active_ids"])
        if not moves:
            domain = [('date', '>=', self.date_from)]
            if self.date_to:
                domain.append(('date', '<=', self.date_to))
            if self.company_id:
                domain.append(('company_id', '=', self.company_id.id))
            moves = self.env['stock.move'].search(domain)
        else:
            if self.date_to and self.company_id:
                moves = moves.filtered(lambda r: r.date >= self.date_from and r.date <= self.date_to and r.company_id == self.company_id.id)
            elif self.date_to and not self.company_id:
                moves = moves.filtered(lambda r: r.date >= self.date_from and r.date <= self.date_to)
            elif not self.date_to and self.company_id:
                moves = moves.filtered(lambda r: r.date >= self.date_from and r.company_id == self.company_id.id)
            else:
                moves = moves.filtered(lambda r: r.date >= self.date_from)
        moves.rebuild_moves(only_remove=self.only_remove)
        return {'type': 'ir.actions.act_window_close'}
