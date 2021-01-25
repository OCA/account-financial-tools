# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    is_initial_balance = fields.Boolean('This is initial balance')
    account_move_line_ids = fields.One2many('account.move.line', 'stock_move_id')

    def _get_accounting_data_for_valuation(self):
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        if self.is_initial_balance:
            opening_move_id = self.company_id.account_opening_move_id
            unaffected_earnings_account = self.company_id.get_unaffected_earnings_account()
            journal_id = opening_move_id.journal_id.id
            acc_src = acc_dest = unaffected_earnings_account.id
            #_logger.info("MOVE %s==>%s:%s:%s:%s" % (opening_move_id, journal_id, acc_src, acc_dest, acc_valuation))
        return journal_id, acc_src, acc_dest, acc_valuation

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        for record in self:
            if record.is_initial_balance:
                opening_move_id = record.company_id.account_opening_move_id
                if not opening_move_id:
                    raise UserError(_('Not opened initial balance'))
                unaffected_earnings_account = record.company_id.get_unaffected_earnings_account()
                _logger.info("MOVE INITIAL %s" % opening_move_id)
                if opening_move_id.state != 'posted' and not opening_move_id.is_initial_balance:
                    opening_move_id.write({'is_initial_balance': True})
                    opening_move_id.post()
                if opening_move_id.state != 'posted' and opening_move_id.is_initial_balance:
                    opening_move_id.post()
                if opening_move_id.state == 'posted':
                    # remove first all old accounting movies
                    acc_moves = False
                    for acc_move in record.account_move_ids:
                        if acc_move.state == 'posted':
                            if not acc_moves:
                                acc_moves = acc_move
                            else:
                                acc_moves |= acc_move
                    if acc_moves:
                        for acc_move in acc_moves:
                            if acc_move.state == 'draft':
                                acc_move.unlink()
                                continue
                            ret = acc_move.button_cancel()
                            if ret:
                                acc_move.unlink()
                    opening_move_id = self.env['account.move'].create({
                        'ref': _('Initial balance - %s' % record.name),
                        'date': opening_move_id.date,
                        'journal_id': opening_move_id.journal_id.id,
                        'is_initial_balance': True,
                        'line_ids': [(0, False, {
                                    'account_id': unaffected_earnings_account.id,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                    })],
                        })
                _logger.info("NEW MOVE INITIAL %s" % opening_move_id)

                quantity = self.env.context.get('forced_quantity', record.product_qty)
                quantity = quantity if record._is_in() else -1 * quantity

                # Make an informative `ref` on the created account move to differentiate between classic
                # movements, vacuum and edition of past moves.
                ref = record.picking_id.name
                if self.env.context.get('force_valuation_amount'):
                    if self.env.context.get('forced_quantity') == 0:
                        ref = 'Revaluation of %s (negative inventory)' % ref
                    elif self.env.context.get('forced_quantity') is not None:
                        ref = 'Correction of %s (modification of past move)' % ref

                move_lines = record.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(record.value), credit_account_id, debit_account_id)
                for line in move_lines:
                    if line[2]['account_id'] != unaffected_earnings_account.id:
                        line[2].update({'stock_move_id': record.id})
                        _logger.info("BALANCE %s" % line[2])
                        balancing_lines = opening_move_id.line_ids.filtered(lambda x: x.account_id == unaffected_earnings_account)
                        balancing_line = balancing_lines._convert_to_write(balancing_lines._cache)
                        balancing_line['debit'] = balancing_line['debit'] > 0 and balancing_line['debit']+line[2]['credit']-line[2]['debit'] or balancing_line['debit']
                        balancing_line['credit'] = balancing_line['credit'] > 0 and balancing_line['credit']+line[2]['debit']-line[2]['credit'] or balancing_line['credit']
                        if balancing_line['debit'] - balancing_line['credit'] == 0 and line[2]['debit']-line[2]['credit'] > 0:
                            balancing_line['credit'] = line[2]['debit']-line[2]['credit']
                        if balancing_line['debit'] - balancing_line['credit'] == 0 and line[2]['credit']-line[2]['debit'] > 0:
                            balancing_line['debit'] = line[2]['credit']-line[2]['debit']
                        debit = balancing_line['debit']
                        credit = balancing_line['credit']
                        if debit < 0.0:
                            balancing_line['debit'] = 0.0
                            balancing_line['credit'] = -debit
                        elif credit < 0.0:
                            balancing_line['debit'] = -credit
                            balancing_line['credit'] = 0.0
                        _logger.info("DISBALANSD dt/ct :: %s" % balancing_line)
                        self.env.cr.execute("UPDATE account_move_line SET debit=%s,credit=%s WHERE id IN (%s)",
                                            (0.0, 0.0, balancing_lines.id,))
                        opening_move_id.with_context(check_move_validity=False).update({'line_ids': [(0, False, line[2]),
                                                                                            (1, balancing_lines.id, balancing_line)]})

                debit_diff, credit_diff = record.company_id.get_opening_move_differences(opening_move_id.line_ids)

                balancing_line = opening_move_id.line_ids.filtered(lambda x: x.account_id == unaffected_earnings_account)

                if balancing_line:
                    if not opening_move_id.line_ids == balancing_line and (debit_diff or credit_diff):
                        balancing_line.debit = credit_diff
                        balancing_line.credit = debit_diff
                    else:
                        opening_move_id.line_ids -= balancing_line
                elif debit_diff or credit_diff:
                    balancing_line = self.env['account.move.line'].new({
                        'name': _('Automatic Balancing Line'),
                        'move_id': opening_move_id.id,
                        'account_id': unaffected_earnings_account.id,
                        'debit': credit_diff,
                        'credit': debit_diff,
                        'company_id': record.company_id,
                    })
                    opening_move_id.line_ids += balancing_line
            else:
                super(StockMove, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _account_entry_move(self):
        if not self._context.get('stop_account_move'):
            super(StockMoveLine, self)._account_entry_move()
