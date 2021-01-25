# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    account_move_ids = fields.One2many('account.move', compute="_compute_account_move_ids")
    accounting_date = fields.Date('Force Accounting Date',
                                  help="Choose the accounting date at which you want to value the stock "
                                       "moves created by the inventory instead of the default one (the "
                                       "inventory end date)")

    @api.onchange
    def _onchange_accounting_date(self):
        if self.accounting_date:
            for move in self.move_lines:
                move.write({'accounting_date': self.accounting_date})
            return {'warning': { 'action': self.action_view_rebuild_account_move()}}

    def action_view_rebuild_account_move(self):
        action = self.env.ref('account_recalculate_stock_move.act_open_wizard_view_stock_picking_add_product').read()[0]
        return action

    def _compute_account_move_ids(self):
        for picking in self:
            if picking.move_lines.mapped("account_move_ids"):
                picking.account_move_ids = False
                for line in picking.move_lines:
                    if not picking.account_move_ids:
                        picking.account_move_ids = line.account_move_ids
                    else:
                        picking.account_move_ids = picking.account_move_ids | line.account_move_ids

    @api.multi
    def action_open_quants(self):
        self.ensure_one()
        products_ids = set(self.move_lines.mapped('product_id').ids)
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', list(products_ids))]
        action['context'] = {'search_default_internal_loc': 1}
        return action

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
    def rebuild_account_move(self):
        for picking in self:
            moves = False
            for move in picking.account_move_ids:
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
            for move in picking.move_lines:
                date = picking.accounting_date or picking.date
                move.write({'date': date, 'accounting_date': date})
                for line in move.move_line_ids:
                    date = move.accounting_date or move.date
                    line.with_context(dict(self.env.context, force_accounting_date=date, force_valuation=True))._rebuild_account_move()

    @api.multi
    def rebuild_picking_move(self):
        for picking in self:
            picking.rebuild_pickings(only_remove=False)

    @api.multi
    def rebuild_pickings(self, only_remove=True):
        for picking in self.filtered(lambda r: r.state == 'done').sorted(lambda r: r.date and r.id):
            moves = False
            for move in picking.account_move_ids:
                if move.state == 'posted':
                    if not moves:
                        moves = move
                    else:
                        moves |= move
            #_logger.info("CANCEL MOVES %s:%s" % (moves, picking))
            if moves:
                for move in moves:
                    if move.state == 'draft':
                        move.unlink()
                        continue
                    ret = move.button_cancel()
                    if ret:
                        move.unlink()
            if not only_remove:
                picking.move_lines.write({"state": 'assigned'})
                picking.write({"state": 'assigned'})
                date = picking.accounting_date or picking.date
                picking.move_lines.write({'accounting_date': date})
                #picking.action_confirm()
                try:
                    picking.with_context(dict(self._context, force_date=date)).button_validate()
                except UserError:
                    _logger.info("PICKING %s unposted" % picking.name)
                    pass
