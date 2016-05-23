# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields


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
