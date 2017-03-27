# -*- coding: utf-8 -*-
# © 2012, Joel Grand-Guillaume, Camptocamp SA.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.multi
    def button_cancel(self):
        """Override the method to add the key 'from_parent_object' in
        the context. This is to allow to delete move line related to
        bank statement through the cancel button.
        """
        self = self.with_context(from_parent_object=True)
        return super(AccountBankStatement, self).button_cancel()

    @api.multi
    def button_confirm_bank(self):
        """Add the from_parent_object key in context in order to be able
        to post the move.
        """
        self = self.with_context(from_parent_object=True)
        return super(AccountBankStatement, self).button_confirm_bank()


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    state = fields.Selection(string='Statement state',
                             related='statement_id.state',
                             default='draft')

    @api.multi
    def cancel(self):
        self = self.with_context(from_parent_object=True)
        return super(AccountBankStatementLine, self).cancel()

    @api.multi
    def process_reconciliation(self, mv_line_dicts):
        """Add the from_parent_object key in context in order to be able
        to balanced the move.
        """
        self = self.with_context(from_parent_object=True)
        return super(AccountBankStatementLine, self)\
            .process_reconciliation(mv_line_dicts)

    @api.multi
    def _is_account_cancel_installed(self):
        ir_module = self.env['ir.module.module']
        res_found_module = ir_module.search_count([
            ('name', '=', 'account_cancel'),
            ('state', '=', 'installed')])
        if res_found_module:
            for line in self:
                line.account_cancel_installed = True

    account_cancel_installed = fields.Boolean(
        compute='_is_account_cancel_installed',
        string='Allow Cancelling Entries')
