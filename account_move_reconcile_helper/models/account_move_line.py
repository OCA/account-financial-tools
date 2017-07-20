# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    partial_reconciliation_in_progress = fields.Boolean(
        compute='_compute_partial_reconciliation_in_progress')
    reconcile_line_ids = fields.One2many(
        compute='_compute_reconciled_lines',
        comodel_name='account.move.line',
        string="Reconciled lines")

    @api.multi
    @api.depends('matched_debit_ids', 'matched_credit_ids')
    def _compute_partial_reconciliation_in_progress(self):
        for rec in self:
            rec.partial_reconciliation_in_progress = (
                bool(rec.matched_debit_ids) or bool(rec.matched_credit_ids))

    @api.multi
    def _compute_reconciled_lines(self):
        for rec in self:
            rec.reconcile_line_ids = rec._get_reconciled_lines()

    @api.multi
    def _get_reconciled_lines(self, move_lines=None):
        """
        Returns lines which were reconciled directly or indirectly with
        current lines given in self.

        If A has been reconciled (or partially) with B, and B with C. This
        method will returns A, B, and C.

        :param move_lines: found moves lines to avoid recursivity
        :return: recordset('account.move.line')
        """
        move_lines = move_lines or self.env[self._name]

        for line in self:
            if line.full_reconcile_id:
                matched_lines = line.full_reconcile_id.reconciled_line_ids
            elif line.credit > 0:
                matched_lines = line.matched_debit_ids.mapped('debit_move_id')
            else:
                matched_lines = line.matched_credit_ids.mapped(
                    'credit_move_id')

            if not matched_lines:
                continue

            move_lines |= line

            for matched_line in matched_lines:
                if matched_line not in move_lines:
                    move_lines |= matched_line
                    move_lines |= matched_line._get_reconciled_lines(
                        move_lines)

        return move_lines

    @api.multi
    def open_full_reconcile_view(self):
        action = self.env.ref('account.action_account_moves_all_a').read()[0]
        action['domain'] = [
            ('id', 'in', self.mapped('reconcile_line_ids').ids)]
        return action
