# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    account_move_line_ids = fields.One2many('account.move.line', related="account_move_id.line_ids")

    @api.multi
    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', '=', self.account_move_id.id)]
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

    def rebuild_account_move(self):
        for cost in self:
            if cost.account_move_id:
                moves = False
                for move in cost.account_move_id:
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
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
            }
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                # Prorate the value at what's still in stock
                cost_to_add = (line.move_id.remaining_qty / line.move_id.product_qty) * line.additional_landed_cost

                new_landed_cost_value = line.move_id.landed_cost_value + line.additional_landed_cost
                line.move_id.write({
                    'landed_cost_value': new_landed_cost_value,
                    'value': line.move_id.value + line.additional_landed_cost,
                    'remaining_value': line.move_id.remaining_value + cost_to_add,
                    'price_unit': (line.move_id.value + line.additional_landed_cost) / line.move_id.product_qty,
                })
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - line.move_id.remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

            move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move.id})
            move.post()
