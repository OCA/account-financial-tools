# Copyright 2011- Slobodni programi d.o.o.
# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.tools import float_is_zero


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('line_ids.debit', 'line_ids.credit',
                 'line_ids.matched_debit_ids.amount',
                 'line_ids.matched_credit_ids.amount',
                 'line_ids.account_id.user_type_id.type')
    def _compute_matched_percentage(self):
        """Compute the percentage to apply for cash basis method.
        This value is relevant only for moves that involve journal items
        on receivable or payable accounts.
        """
        storno_moves = self.filtered(
            lambda m: m.journal_id.posting_policy == 'storno')
        contra_moves = self - storno_moves
        for move in storno_moves:
            total_amount = 0.0
            total_reconciled = 0.0
            for line in move.line_ids:
                if line.account_id.user_type_id.type in (
                        'receivable', 'payable'):
                    amount = line.debit + line.credit
                    sign = 1 if amount > 0 else -1
                    total_amount += amount
                    for partial_line in (line.matched_debit_ids +
                                         line.matched_credit_ids):
                        total_reconciled += sign * partial_line.amount
            if float_is_zero(total_amount,
                             precision_rounding=move.currency_id.rounding):
                move.matched_percentage = 1.0
            else:
                move.matched_percentage = total_reconciled / total_amount
        super(AccountMove, contra_moves)._compute_matched_percentage()

    @api.multi
    def _reverse_move(self, date=None, journal_id=None):
        self.ensure_one()
        if self.journal_id.posting_policy == 'storno':
            reversed_move = self.copy(default={
                'date': date,
                'journal_id':
                    journal_id.id if journal_id else self.journal_id.id,
                'ref': _('Storno of: ') + self.name})
            for acm_line in reversed_move.line_ids.with_context(
                    check_move_validity=False):
                acm_line.write({
                    'debit': -acm_line.debit,
                    'credit': -acm_line.credit,
                    'amount_currency': -acm_line.amount_currency
                })
            return reversed_move
        return super(AccountMove, self)._reverse_move(date, journal_id)
