# Copyright 2018 PESOL (<https://www.pesol.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields


class AccountMoveTrigger(models.Model):
    _name = 'account.move.trigger'
    _rec_name = 'account_id'
    _description = "Account Move Trigger"

    name = fields.Char(
        string='Name',
        required=True)
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Trigger Account',
        required=True)
    move_type = fields.Selection(
        [('debit', 'Debit'),
         ('credit', 'Credit')],
        string='Trigger Move Type',
        required=True)
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        required=True)
    debit_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Debit Account',
        required=True)
    credit_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Credit Account',
        required=True)
    auto_reconcile = fields.Boolean(
        string='Auto Reconcile')


    @api.multi
    def trigger(self, line):
        ref = line.move_id.ref
        amount = line.debit or line.credit
        move_obj = self.env['account.move']
        for move in self:
            debit_values = {
                'account_id': move.debit_account_id.id,
                'debit': amount,
                'tirggered_from_id': line.credit and line.id,
                'date_maturity': line.date_maturity,
                'auto_reconcile': self.auto_reconcile
            }
            credit_values = {
                'account_id': move.credit_account_id.id,
                'credit': amount,
                'tirggered_from_id': line.debit and  line.id,
                'date_maturity': line.date_maturity,
                'auto_reconcile': self.auto_reconcile
            }
            move = move_obj.create({
                'journal_id': move.journal_id.id,
                'ref': '%s: %s' % (move.name, ref or ''),
                'line_ids': [(0, 0, debit_values), (0, 0, credit_values)]
            })
            move.post()

    @api.model
    def do_auto_reconcile(self):
        today = fields.Date.today()
        to_reconcile = self.env['account.move.line'].search([
            ('tirggered_from_id', '!=', False),
            ('full_reconcile_id', '=', False),
            ('balance','!=', 0),
            ('account_id.reconcile','=',True),
            ('date_maturity', '<=', today)
        ])
        for line in to_reconcile:
            move_lines = self.env['account.move.line']
            move_lines += line
            move_lines += line.tirggered_from_id
            move_lines.force_full_reconcile()


class AccountAccount(models.Model):
    _inherit = 'account.account'

    trigger_account_ids = fields.One2many(
        comodel_name='account.move.trigger',
        inverse_name='account_id',
        string='Account Move Trigger')
