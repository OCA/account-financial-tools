# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.addons.stock_landed_costs.models.stock_landed_cost import AdjustmentLines as adjustmentlines

import logging

_logger = logging.getLogger(__name__)


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


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    def _create_accounting_entries(self, move, qty_out):
        # TDE CLEANME: product chosen for computation ?
        cost_product = self.cost_line_id.product_id
        if not cost_product:
            return False
        accounts = self.product_id.product_tmpl_id.get_product_accounts()
        debit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id or False
        # If the stock move is dropshipped move we need to get the cost account instead the stock valuation account
        if self.move_id._is_dropshipped():
            debit_account_id = accounts.get('stock_output') and accounts['stock_output'].id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = self.cost_line_id.account_id.id or cost_product.property_account_expense_id.id or cost_product.categ_id.property_account_expense_categ_id.id

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))
        return self._create_account_move_line(move, credit_account_id, debit_account_id, qty_out, already_out_account_id)

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = []

        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id, product_id=self.cost_line_id.product_id.id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.append([0, 0, debit_line])
        AccountMoveLine.append([0, 0, credit_line])

        # Create account move lines for quants already out of stock
        if qty_out > 0:
            debit_line = dict(base_line,
                              name=(self.name + ": " + str(qty_out) + _(' already out')),
                              quantity=0,
                              account_id=already_out_account_id)
            credit_line = dict(base_line,
                               name=(self.name + ": " + str(qty_out) + _(' already out')),
                               quantity=0,
                               account_id=debit_account_id)
            diff = diff * qty_out / self.quantity
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            AccountMoveLine.append([0, 0, debit_line])
            AccountMoveLine.append([0, 0, credit_line])

            # TDE FIXME: oh dear
            if self.env.user.company_id.anglo_saxon_accounting:
                debit_line = dict(base_line,
                                  name=(self.name + ": " + str(qty_out) + _(' already out')),
                                  quantity=0,
                                  account_id=credit_account_id)
                credit_line = dict(base_line,
                                   name=(self.name + ": " + str(qty_out) + _(' already out')),
                                   quantity=0,
                                   account_id=already_out_account_id)

                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                AccountMoveLine.append([0, 0, debit_line])
                AccountMoveLine.append([0, 0, credit_line])

        return AccountMoveLine


adjustmentlines._create_accounting_entries = AdjustmentLines._create_accounting_entries
adjustmentlines._create_accounting_entries = AdjustmentLines._create_account_move_line
