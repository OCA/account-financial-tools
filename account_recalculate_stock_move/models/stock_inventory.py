# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class Inventory(models.Model):
    _inherit = "stock.inventory"

    is_force_accounting_date = fields.Boolean('Forced Accounting Date')
    account_move_ids = fields.One2many('account.move', compute="_compute_account_move_ids")

    def _compute_account_move_ids(self):
        for inventory in self:
            if inventory.move_ids.mapped("account_move_ids"):
                inventory.account_move_ids = False
                for line in inventory.move_ids:
                    if not inventory.account_move_ids:
                        inventory.account_move_ids = line.account_move_ids
                    else:
                        inventory.account_move_ids = inventory.account_move_ids | line.account_move_ids

    @api.multi
    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_ids.ids)]
        action_data['context'] = {'search_default_misc_filter':0, 'view_no_maturity': True}
        return action_data

    @api.multi
    def _rebuild_account_move(self):
        for move in self.move_ids:
            if (not move.account_move_ids or self.is_force_accounting_date) and move.state == 'done' and self.env.context.get("rebuld_try"):
                try:
                    for line in move.move_line_ids:
                        line.with_context(dict(self.env.context, force_valuation=True))._rebuild_account_move()
                except:
                    pass
            elif (not move.account_move_ids or self.is_force_accounting_date) and move.state == 'done' and not self.env.context.get("rebuld_try"):
                for line in move.move_line_ids:
                    line.with_context(dict(self.env.context, force_valuation=True))._rebuild_account_move()

    def rebuild_account_move(self):
        if len(self.move_ids.ids) > 0:
            if self.is_force_accounting_date:
                moves = False
                for move in self.account_move_ids:
                    if move.state == 'posted':
                        if not moves:
                            moves = move
                        else:
                            moves |= move
                if moves:
                    for move in moves:
                        ret = move.button_cancel()
                        if ret:
                            move.unlink()
                for line in self.move_ids:
                    date = self.accounting_date or self.date
                    line.write({"date": date})
                    line.move_line_ids.write({"date": date})
            self._rebuild_account_move()
        else:
            raise Warning(_("On this inventory is not have movement."))

    @api.multi
    def action_cancel(self):
        for inventory in self:
            moves = False
            for move in inventory.account_move_ids:
                if move.state == 'posted':
                    if not moves:
                        moves = move
                    else:
                        moves |= move
            if moves:
                for move in moves:
                    ret = move.button_cancel()
                    if ret:
                        move.unlink()
            for moves_to_unlink in inventory.move_ids:
                moves_to_unlink._clean_merged()
                moves_to_unlink.write({"state": 'draft'})
                moves_to_unlink.move_line_ids.write({"qty_done": 0.0})
                moves_to_unlink._action_cancel()
                moves_to_unlink.sudo().unlink()
            if not inventory.account_move_ids and not inventory.move_ids:
                inventory.state = 'cancel'

    @api.multi
    def action_cancel_and_delete(self, remove_after=False):
        self.action_cancel()
        if remove_after:
            for record in self:
                record.unlink()
