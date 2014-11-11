# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp


class AccountStatementOperationRule(models.Model):
    _name = 'account.statement.operation.rule'

    name = fields.Char()
    operations = fields.Many2many(
        comodel_name='account.statement.operation.template',
        relation='account_statement_oper_rule_rel',
    )
    amount_min = fields.Float(
        string='Min. Amount',
        digits=dp.get_precision('Account'),
    )
    amount_max = fields.Float(
        string='Max. Amount',
        digits=dp.get_precision('Account'),
    )
    multicurrency = fields.Boolean(
        help="The balance is different, but the balance in currency is "
             "the same, so it is a currency rate difference.",
    )
    sequence = fields.Integer(
        default=10,
        help="If several rules match, the first one is used.")

    @api.model
    @api.returns('account.statement.operation.template')
    def operations_for_reconciliation(self, statement_line,
                                      selected_lines,
                                      balance):
        line_obj = self.env['account.bank.statement.line']
        line = line_obj.browse(statement_line['id'])

        multicurrency = False
        if line.currency_id != line.company_id.currency_id:
            amount_currency = statement_line.amount_currency
            select_line_ids = (l['id'] for l in selected_lines)
            for select_line in line_obj.browse(select_line_ids):
                # TODO different currencies possible?
                amount_currency -= select_line.amount_currency

            # amount in currency is the same, so the balance is
            # a difference due to currency rates
            if line.currency_id.is_zero():
                multicurrency = True

        rules = self.search([('amount_min', '<=', balance),
                             ('amount_max', '>=', balance),
                             ('multicurrency', '=', multicurrency)],
                            limit=1)
        return rules.operations
