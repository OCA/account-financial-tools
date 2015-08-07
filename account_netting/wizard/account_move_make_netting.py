# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, exceptions, _


class AccountMoveMakeNetting(models.TransientModel):
    _name = "account.move.make.netting"

    journal = fields.Many2one(
        comodel_name="account.journal", required=True,
        domain="[('type', '=', 'general')]")
    move_lines = fields.Many2many(comodel_name="account.move.line")
    balance = fields.Float(readonly=True)
    balance_type = fields.Selection(
        selection=[('pay', 'To pay'), ('receive', 'To receive')],
        readonly=True)

    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', [])) < 2:
            raise exceptions.ValidationError(
                _("You should compensate at least 2 journal entries."))
        move_lines = self.env['account.move.line'].browse(
            self.env.context['active_ids'])
        if (any(x not in ('payable', 'receivable') for
                x in move_lines.mapped('account_id.type'))):
            raise exceptions.ValidationError(
                _("All entries must have a receivable or payable account"))
        if any(move_lines.mapped('reconcile_id')):
            raise exceptions.ValidationError(
                _("All entries mustn't been reconciled"))
        partner_id = None
        for move in move_lines:
            if (not move.partner_id or (
                    move.partner_id != partner_id and partner_id is not None)):
                raise exceptions.ValidationError(
                    _("All entries should have a partner and the partner must "
                      "be the same for all."))
            partner_id = move.partner_id
        res = super(AccountMoveMakeNetting, self).default_get(fields)
        res['move_lines'] = [(6, 0, move_lines.ids)]
        balance = (sum(move_lines.mapped('debit')) -
                   sum(move_lines.mapped('credit')))
        res['balance'] = abs(balance)
        res['balance_type'] = 'pay' if balance < 0 else 'receive'
        return res

    @api.multi
    def button_compensate(self):
        self.ensure_one()
        # Create account move
        move = self.env['account.move'].create(
            {
                'ref': _('AR/AP netting'),
                'journal_id': self.journal.id,
            })
        # Group amounts by account
        account_groups = self.move_lines.read_group(
            [('id', 'in', self.move_lines.ids)],
            ['account_id', 'debit', 'credit'], ['account_id'])
        debtors = []
        creditors = []
        total_debtors = 0
        total_creditors = 0
        for account_group in account_groups:
            balance = account_group['debit'] - account_group['credit']
            group_vals = {
                'account_id': account_group['account_id'][0],
                'balance': abs(balance),
            }
            if balance > 0:
                debtors.append(group_vals)
                total_debtors += balance
            else:
                creditors.append(group_vals)
                total_creditors += abs(balance)
        # Create move lines
        move_line_model = self.env['account.move.line']
        netting_amount = min(total_creditors, total_debtors)
        field_map = {1: 'debit', 0: 'credit'}
        for i, group in enumerate([debtors, creditors]):
            available_amount = netting_amount
            for account_group in group:
                if account_group['balance'] > available_amount:
                    amount = available_amount
                else:
                    amount = account_group['balance']
                move_line_vals = {
                    field_map[i]: amount,
                    'move_id': move.id,
                    'partner_id': self.move_lines[0].partner_id.id,
                    'date': move.date,
                    'period_id': move.period_id.id,
                    'journal_id': move.journal_id.id,
                    'name': move.ref,
                    'account_id': account_group['account_id'],
                }
                move_line_model.create(move_line_vals)
                available_amount -= account_group['balance']
                if available_amount <= 0:
                    break
        # Make reconciliation
        for move_line in move.line_id:
            to_reconcile = move_line + self.move_lines.filtered(
                lambda x: x.account_id == move_line.account_id)
            to_reconcile.reconcile_partial()
        # Open created move
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['view_mode'] = 'form'
        del action['views']
        del action['view_id']
        action['res_id'] = move.id
        return action
