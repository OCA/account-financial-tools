# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _rebuild_account_move(self):
        move = self.move_id
        if move.state == 'done':
            move._run_valuation(self.qty_done)
            if self._context.get("force_accounting_date"):
                date = self._context['force_accounting_date']
            else:
                date = move.accounting_date or move.date or fields.Date.context_today(self)
            if move.product_id.valuation == 'real_time' and (move._is_in() or move._is_out()):
                amount = self.qty_done * abs(move.price_unit)
                if move._is_in():
                    amount = -amount
                move.with_context(forced_quantity=self.qty_done, force_valuation_amount=amount,
                                  force_period_date=date)._account_entry_move()

    @api.multi
    def write(self, vals):
        res = super(StockMoveLine, self).write(vals)
        if 'product_id' in vals:
            for move_line in self:
                move = move_line.move_id
                if move.company_id.currency_id.is_zero(
                        move_line.price_unit) and not move_line.location_id._should_be_valued() and not move_line.location_dest_id._should_be_valued():
                    move_line.price_unit = move._get_price_unit()
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    has_account_move = fields.Boolean(compute="_compute_has_account_move")
    accounting_date = fields.Date('Force Accounting Date',
                                  help="Choose the accounting date at which you want to value the stock "
                                       "moves created by the inventory instead of the default one (the "
                                       "inventory end date)")

    @api.depends('account_move_ids')
    def _compute_has_account_move(self):
        for move in self:
            move.has_account_move = len(move.account_move_ids.ids) > 0

    @api.multi
    def _rebuild_account_move(self):
        for move in self:
            if not move.account_move_ids and move.state == 'done' and self.env.context.get("rebuld_try"):
                try:
                    for line in move.move_line_ids:
                        line._rebuild_account_move()
                except:
                    pass
            elif not move.account_move_ids and move.state == 'done' and not self.env.context.get("rebuld_try"):
                for line in move.move_line_ids:
                    line._rebuild_account_move()

    def rebuild_account_move(self):
        if not self.account_move_ids and self.state == 'done' and self.product_id.valuation == 'real_time' and (
                self._is_in() or self._is_out()):
            self._rebuild_account_move()
        else:
            state = (self.state == 'done') and " " or "*"
            real_time = (self.product_id.valuation == 'real_time') and " " or "*"
            in_out = (self._is_in() or self._is_out()) and " " or "*"
            raise Warning(_(
                "The operation will not be performed because one of the following conditions may not have been met: \n\n %s1. Status not in \"Done\" \n%s2. The spelling in the product or its category is not in real time.\n%s3. This is not a movement at the entrance or exit of the company.") % (
                              state, real_time, in_out))

    def write(self, vals):
        if (vals.get('state', '') == 'done' and vals.get('date')):
            vals['accounting_date'] = vals['date']
        return super(StockMove, self).write(vals)
