# Copyright 2016-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AccountInvoiceSpreadLine(models.Model):
    _name = 'account.spread.line'
    _description = 'Account Spread Lines'
    _order = 'date'

    name = fields.Char('Description', readonly=True)
    amount = fields.Float(digits=dp.get_precision('Account'), required=True)
    date = fields.Date(required=True)
    spread_id = fields.Many2one(
        'account.spread', string='Spread Board', ondelete='cascade')
    move_id = fields.Many2one(
        'account.move', string='Journal Entry', readonly=True)

    @api.multi
    def create_and_reconcile_moves(self):
        grouped_lines = {}
        for spread_line in self:
            spread = spread_line.spread_id
            spread_line_list = grouped_lines.get(
                spread, self.env['account.spread.line'])
            grouped_lines.update({
                spread: spread_line_list + spread_line
            })
        for spread in grouped_lines:
            created_moves = grouped_lines[spread]._create_moves()

            if created_moves:
                post_msg = _("Created move(s) ")
                post_msg += ", ".join(
                    '<a href=# data-oe-model=account.move data-oe-id=%d'
                    '>%s</a>' % (move.id, move.name)
                    for move in created_moves)
                spread.message_post(body=post_msg)

            spread._reconcile_spread_moves(created_moves)
            self._post_spread_moves(spread, created_moves)

    @api.model
    def _post_spread_moves(self, spread, moves):
        if not moves:
            return
        if spread.company_id.force_move_auto_post:
            moves.post()
        elif spread.move_line_auto_post:
            moves.post()

    @api.multi
    def create_move(self):
        """Button to manually create a move from a spread line entry.
        """
        self.ensure_one()
        self.create_and_reconcile_moves()

    @api.multi
    def _create_moves(self):
        if self.filtered(lambda l: l.move_id):
            raise UserError(_('This spread line is already linked to a '
                              'journal entry! Please post or delete it.'))

        created_moves = self.env['account.move']
        for line in self:
            move_vals = line._prepare_move()
            move = self.env['account.move'].create(move_vals)

            line.write({'move_id': move.id})
            created_moves += move
        return created_moves

    @api.multi
    def _prepare_move(self):
        self.ensure_one()

        spread_date = self.env.context.get('spread_date') or self.date
        spread = self.spread_id
        analytic = spread.account_analytic_id
        analytic_tags = [(4, tag.id, None) for tag in spread.analytic_tag_ids]

        company_currency = spread.company_id.currency_id
        current_currency = spread.currency_id
        not_same_curr = company_currency != current_currency
        amount = current_currency._convert(
            self.amount, company_currency, spread.company_id, spread_date)

        line_ids = [(0, 0, {
            'name': spread.name.split('\n')[0][:64],
            'account_id': spread.debit_account_id.id,
            'debit': amount if amount > 0.0 else 0.0,
            'credit': -amount if amount < 0.0 else 0.0,
            'partner_id': self.spread_id.invoice_id.partner_id.id,
            'analytic_account_id': analytic.id,
            'analytic_tag_ids': analytic_tags,
            'currency_id': not_same_curr and current_currency.id or False,
            'amount_currency': not_same_curr and - 1.0 * self.amount or 0.0,
        }), (0, 0, {
            'name': spread.name.split('\n')[0][:64],
            'account_id': spread.credit_account_id.id,
            'credit': amount if amount > 0.0 else 0.0,
            'debit': -amount if amount < 0.0 else 0.0,
            'partner_id': self.spread_id.invoice_id.partner_id.id,
            'analytic_account_id': analytic.id,
            'analytic_tag_ids': analytic_tags,
            'currency_id': not_same_curr and current_currency.id or False,
            'amount_currency': not_same_curr and self.amount or 0.0,
        })]

        return {
            'name': self.name or "/",
            'ref': self.name,
            'date': spread_date,
            'journal_id': spread.journal_id.id,
            'line_ids': line_ids,
            'company_id': spread.company_id.id,
        }

    @api.multi
    def open_move(self):
        """Used by a button to manually view a move from a
        spread line entry.
        """
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'res_id': self.move_id.id,
        }

    @api.multi
    def unlink_move(self):
        """Used by a button to manually unlink a move
        from a spread line entry.
        """
        for line in self:
            move = line.move_id
            if move.state == 'posted':
                move.button_cancel()
            move.line_ids.remove_move_reconcile()
            post_msg = _("Deleted move %s") % line.move_id.id
            move.unlink()
            line.move_id = False
            line.spread_id.message_post(body=post_msg)

    @api.model
    def _create_entries(self):
        """Find spread line entries where date is in the past and
        create moves for them. Method also called by the cron job.
        """
        lines = self.search([
            ('date', '<=', fields.Date.today()),
            ('move_id', '=', False)
        ])
        lines.create_and_reconcile_moves()

        unposted_moves = self.search([('move_id', '!=', False)]).mapped(
            'move_id').filtered(lambda m: m.state != 'posted')
        unposted_moves.filtered(
            lambda m: m.company_id.force_move_auto_post).post()

        spreads_to_archive = self.env['account.spread'].search([
            ('all_posted', '=', True)
        ]).filtered(lambda s: s.company_id.auto_archive)
        spreads_to_archive.write({'active': False})
