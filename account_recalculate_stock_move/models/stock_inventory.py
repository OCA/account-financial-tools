# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
#from odoo.addons.stock.models.stock_inventory import Inventory as inventory
from odoo.exceptions import UserError, Warning

import logging
_logger = logging.getLogger(__name__)


class Inventory(models.Model):
    _inherit = "stock.inventory"

    #is_force_accounting_date = fields.Boolean('Forced Accounting Date')
    account_move_ids = fields.One2many('account.move', compute="_compute_account_move_ids")
    account_move_line_ids = fields.One2many('account.move.line', compute="_compute_account_move_line_ids")

    def _compute_account_move_ids(self):
        for inventory in self:
            if inventory.move_ids.mapped("account_move_ids"):
                inventory.account_move_ids = False
                for line in inventory.move_ids:
                    if not inventory.account_move_ids:
                        inventory.account_move_ids = line.account_move_ids
                    else:
                        inventory.account_move_ids = inventory.account_move_ids | line.account_move_ids

    def _compute_account_move_line_ids(self):
        for inventory in self:
            if inventory.move_ids.mapped("account_move_line_ids"):
                inventory.account_move_line_ids = False
                for line in inventory.move_ids:
                    if not inventory.account_move_line_ids:
                        inventory.account_move_line_ids = line.account_move_line_ids
                    else:
                        inventory.account_move_line_ids |= line.account_move_line_ids

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
    def action_get_account_move_lines(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_account_moves_all_a')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_line_ids.ids)]
        action_data['context'] = {'search_default_movegroup': 1}
        return action_data

    @api.multi
    def _rebuild_account_move(self):
        for record in self:
            for move in record.move_ids:
                if not move.account_move_ids and move.state == 'done' and self.env.context.get("rebuld_try"):
                    if self.env.context.get('force_accounting_date'):
                        move.write({'date': self.env.context['force_accounting_date'], 'accounting_date': self.env.context['force_accounting_date']})
                    try:
                        for line in move.move_line_ids:
                            line.with_context(dict(self.env.context, force_valuation=True))._rebuild_account_move()
                    except UserError:
                        _logger.info("STOCK MOVE %s unposted" % move.name)
                        pass
                elif not move.account_move_ids and move.state == 'done' and not self.env.context.get("rebuld_try"):
                    if self.env.context.get('force_accounting_date'):
                        move.write({'date': self.env.context['force_accounting_date'], 'accounting_date': self.env.context['force_accounting_date']})
                    for line in move.move_line_ids:
                        line.with_context(dict(self.env.context, force_valuation=True))._rebuild_account_move()

    @api.multi
    def rebuild_account_move(self):
        for record in self:
            date = record.accounting_date or record.date

            if len(record.move_ids.ids) > 0:
                #if self.is_force_accounting_date:
                #date = record.date
                #if record.is_force_accounting_date:

                moves = False
                for move in record.account_move_ids:
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
                record.with_context(dict(self._context, force_accounting_date=date, force_valuation=True))._rebuild_account_move()
            else:
                try:
                    for inventory in self.filtered(lambda x: x.state in ('done')):
                        inventory.line_ids._generate_moves()
                except:
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

    def post_inventory(self):
        self.mapped('move_ids').filtered(lambda move: move.state != 'done' and move.only_quantity).write({'price_unit': 0.0})
        return super(Inventory, self).post_inventory()


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    only_quantity = fields.Boolean('No amount', help='Do not use amount for accounting entries')

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super()._get_move_values(qty, location_id, location_dest_id, out)
        res['only_quantity'] = self.only_quantity
        return res
