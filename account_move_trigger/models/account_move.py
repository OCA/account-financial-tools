# Copyright 2018 PESOL (<https://www.pesol.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tirggered_from_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Triggered From')
    auto_reconcile = fields.Boolean(
        string='Auto Reconcile')

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        trigger_account_obj = self.env['account.move.trigger']
        trigger_accounts = trigger_account_obj.search([])
        trigger_account_list = trigger_accounts.mapped(
            lambda t: (t.account_id.id, t.move_type)
        )
        for line in self.mapped('line_ids').filtered(
                lambda l: (l.account_id.id, l.debit and 'debit' or 'credit') in
                trigger_account_list
        ):
            line.account_id.trigger_account_ids.trigger(line)

        return super(AccountMove, self).post()
