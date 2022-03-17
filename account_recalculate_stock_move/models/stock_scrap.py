# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    account_move_ids = fields.One2many('account.move', compute="_compute_account_move_ids")
    account_move_line_ids = fields.One2many('account.move.line', compute="_compute_account_move_line_ids")
    accounting_date = fields.Date('Force Accounting Date',
                                  help="Choose the accounting date at which you want to value the stock "
                                       "moves created by the inventory instead of the default one (the "
                                       "inventory end date)")

    def _compute_account_move_ids(self):
        for scrap in self:
            if scrap.move_id.mapped("account_move_ids"):
                scrap.account_move_ids = False
                for line in scrap.move_id:
                    if not scrap.account_move_ids:
                        scrap.account_move_ids = line.account_move_ids
                    else:
                        scrap.account_move_ids = scrap.account_move_ids | line.account_move_ids

    def _compute_account_move_line_ids(self):
        for scrap in self:
            if scrap.move_id.mapped("account_move_line_ids"):
                scrap.account_move_line_ids = False
                for line in scrap.move_id:
                    if not scrap.account_move_line_ids:
                        scrap.account_move_line_ids = line.account_move_line_ids
                    else:
                        scrap.account_move_line_ids |= line.account_move_line_ids

    def _prepare_move_values(self):
        vals = super(StockScrap, self)._prepare_move_values()
        self.ensure_one()
        if self.accounting_date:
            vals.update({
                'accounting_date': self.accounting_date,
            })
        return vals

    @api.multi
    def rebuild_account_move(self):
        for scrap in self:
            moves = False
            for move in scrap.account_move_ids:
                if move.state == 'posted':
                    if not moves:
                        moves = move
                    else:
                        moves |= move
            if moves:
                for move in moves:
                    if move.state == 'draft':
                        move.unlink()
                        continue
                    ret = move.button_cancel()
                    if ret:
                        move.unlink()
            for line in scrap.move_id:
                date = scrap.accounting_date or line.date
                line.with_context(dict(self.env.context, force_accounting_date=date,
                                       force_valuation=True))._rebuild_account_move()

    @api.multi
    def action_get_account_move_lines(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_account_moves_all_a')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_line_ids.ids)]
        action_data['context'] = {'search_default_movegroup': 1}
        return action_data
