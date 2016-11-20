# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# (c) 2016 Noviat nv/sa (www.noviat.com)
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
            ['account_id', 'debit', 'credit',
             'currency_id', 'amount_currency'],
            ['currency_id', 'account_id'],
            lazy=False)
        debtors = {}
        creditors = {}
        total_debtors = {}
        total_creditors = {}
        currency_ids = []
        for account_group in account_groups:
            balance = account_group['debit'] - account_group['credit']
            group_vals = {
                'account_id': account_group['account_id'][0],
                'balance': abs(balance),
            }
            currency_id = account_group['currency_id'] \
                and account_group['currency_id'][0] or False
            if currency_id not in currency_ids:
                currency_ids.append(currency_id)
            if currency_id:
                group_vals.update({
                    'currency_id': currency_id,
                    'amount_currency': account_group['amount_currency'],
                })
            if balance > 0:
                if currency_id in total_debtors:
                    debtors[currency_id].append(group_vals)
                    total_debtors[currency_id]['balance'] += balance
                    if currency_id:
                        total_debtors[currency_id]['balance_currency'] += \
                            account_group['amount_currency']
                else:
                    debtors[currency_id] = [group_vals]
                    total_debtors[currency_id] = {'balance': balance}
                    if currency_id:
                        total_debtors[currency_id]['balance_currency'] = \
                            account_group['amount_currency']
            else:
                if currency_id in total_creditors:
                    creditors[currency_id].append(group_vals)
                    total_creditors[currency_id]['balance'] += abs(balance)
                    if currency_id:
                        total_creditors[currency_id]['balance_currency'] += \
                            account_group['amount_currency']
                else:
                    creditors[currency_id] = [group_vals]
                    total_creditors[currency_id] = {'balance': abs(balance)}
                    if currency_id:
                        total_creditors[currency_id]['balance_currency'] = \
                            account_group['amount_currency']
        # Create move lines
        move_line_model = self.env['account.move.line']
        field_map = {1: 'debit', 0: 'credit'}
        for currency_id in currency_ids:
            if total_debtors[currency_id]['balance'] \
                    < total_creditors[currency_id]['balance']:
                netting_amount = total_debtors[currency_id]['balance']
                if currency_id:
                    netting_amount_currency = \
                        total_debtors[currency_id]['balance_currency']
            else:
                netting_amount = total_creditors[currency_id]['balance']
                netting_amount_currency = \
                    total_creditors[currency_id]['balance_currency']
            for i, group in enumerate(
                    [debtors[currency_id], creditors[currency_id]]):
                available_amount = netting_amount
                if currency_id:
                    available_amount_currency = netting_amount_currency
                for account_group in group:
                    balance = account_group['balance']
                    if balance > available_amount:
                        amount = available_amount
                        if currency_id:
                            amount_currency = -available_amount_currency
                    else:
                        amount = balance
                        if currency_id:
                            amount_currency = -account_group['amount_currency']
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
                    if currency_id:
                        sign = i == 0 and 1 or -1
                        move_line_vals.update({
                            'currency_id': account_group['currency_id'],
                            'amount_currency': sign * amount_currency,
                        })
                    move_line_model.create(move_line_vals)
                    available_amount -= balance
                    if currency_id:
                        available_amount_currency -= \
                            account_group['amount_currency']
                    if available_amount <= 0:
                        break
        # Make reconciliation
        for move_line in move.line_id:
            to_reconcile = move_line + self.move_lines.filtered(
                lambda x:
                x.account_id == move_line.account_id
                and x.currency_id == move_line.currency_id)
            to_reconcile.reconcile_partial()
        # Open created move
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['view_mode'] = 'form'
        del action['views']
        del action['view_id']
        action['res_id'] = move.id
        return action
