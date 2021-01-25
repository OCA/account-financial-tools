# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class Inventory(models.Model):
    _inherit = "stock.inventory"

    is_initial_balance = fields.Boolean('This is initial balance')
    future_initial_balance = fields.Boolean('Mark for initial balance')
    stop_account_move = fields.Boolean('Block account move')

    @api.multi
    def background_toggle_is_initial_balance(self):
        for record in self.search([('future_initial_balance', '=', True)]):
            _logger.info("Started future initial balance for %s" % record.name)
            if record.future_initial_balance and not record.is_initial_balance:
                record.write({'is_initial_balance': True, 'future_initial_balance': False})
                record._delete_inital_moves()
                date = record.company_id.account_opening_move_id.date
                super(Inventory, self.with_context(
                    dict(self._context, force_accounting_date=date, force_period_date=date))).rebuild_account_move()
            else:
                _logger.info("Ignore toggle for %s" % record.name)

    @api.multi
    def toggle_is_initial_balance(self):
        self.ensure_one()
        self.is_initial_balance = not self.is_initial_balance
        for line in self.move_ids:
            line.write({'is_initial_balance': self.is_initial_balance})
        if self.is_initial_balance:
            date = self.company_id.account_opening_move_id.date
            self.with_context(dict(self._context, force_accounting_date=date, force_period_date=date, skip_delete=True)).rebuild_account_move()
        else:
            self._delete_inital_moves()
            self.rebuild_account_move()

    @api.multi
    def _delete_inital_moves(self):
        for record in self:
            account_line_delete = self.env['account.move.line']
            unaffected_earnings_account = record.company_id.get_unaffected_earnings_account()

            for line in record.move_ids:
                account_line_delete += line.account_move_line_ids
            if len(account_line_delete.ids) > 0:
                opening_move_id = record.company_id.account_opening_move_id

                debit_diff, credit_diff = record.company_id.get_opening_move_differences(opening_move_id.line_ids)
                _logger.info("DISBALANSED 1 %s::%s" % (debit_diff, credit_diff))

                balancing_lines = opening_move_id.line_ids.filtered(lambda x: x.account_id == unaffected_earnings_account)
                balancing_line = balancing_lines._convert_to_write(balancing_lines._cache)

                for line in account_line_delete:
                    line_for_delete = line._convert_to_write(line._cache)
                    _logger.info("BALANSE %s" % line_for_delete)
                    balancing_line['debit'] = balancing_line['debit'] > 0 and balancing_line['debit'] + line_for_delete['debit'] - line_for_delete['credit'] or \
                                              balancing_line['debit']
                    balancing_line['credit'] = balancing_line['credit'] > 0 and balancing_line['credit'] - line_for_delete['credit'] - line_for_delete['debit'] or \
                                               balancing_line['credit']
                    debit = balancing_line['debit']
                    credit = balancing_line['credit']
                    if debit < 0.0:
                        balancing_line['credit'] = -debit
                        balancing_line['debit'] = 0.0
                    elif credit < 0.0:
                        balancing_line['debit'] = -credit
                        balancing_line['credit'] = 0.0
                    _logger.info("BALANCE %s:%s::%s:%s" % (balancing_line['debit'], balancing_lines.debit, balancing_line['credit'], balancing_lines.credit))
                    self.env.cr.execute("UPDATE account_move_line SET debit=%s,credit=%s WHERE id IN (%s)",
                                        (0.0, 0.0, balancing_lines.id,))
                    #opening_move_id.with_context(check_move_validity=False).line_ids -= line
                    opening_move_id.with_context(check_move_validity=False).write({'line_ids': [(2, line.id), (1, balancing_lines.id, balancing_line)]})

    def rebuild_account_move(self):
        for record in self:
            if record.is_initial_balance and self._context.get('skip_delete', False):
                record._delete_inital_moves()
                date = record.company_id.account_opening_move_id.date
                super(Inventory, self.with_context(
                    dict(self._context, force_accounting_date=date, force_period_date=date))).rebuild_account_move()
            else:
                super(Inventory, self).rebuild_account_move()

    def post_inventory(self):
        if self.stop_account_move:
            self = self.with_context(dict(self._context, stop_account_move=self.stop_account_move))
        return super(Inventory, self).post_inventory()


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super()._get_move_values(qty, location_id, location_dest_id, out)
        res['is_initial_balance'] = self.inventory_id.is_initial_balance
        return res
