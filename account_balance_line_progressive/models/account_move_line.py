# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _order = 'date desc, id desc'

    @api.depends('debit', 'credit')
    def _compute_balance_progressive(self):
        tables, where_clause, where_params = self.with_context(
            initial_bal=True)._query_get()
        where_params = [tuple(self.ids)] + where_params
        query = """SELECT l1.id, COALESCE(SUM(l2.debit-l2.credit), 0)
            FROM account_move_line l1
            LEFT JOIN account_account a
            ON (a.id = l1.account_id)
            LEFT JOIN account_account_type at
            ON (at.id = a.user_type_id)
            JOIN account_move m on (m.id = l1.move_id AND m.state <> 'draft')
            LEFT JOIN account_move_line l2
            ON (l1.account_id = l2.account_id
                AND (
                     l1.partner_id = l2.partner_id
                     OR
                     at.type not in ('receivable', 'payable')
                    )
               )
            AND (l2.date < l1.date OR (l2.date = l1.date AND l2.id <= l1.id))
            WHERE l1.id IN %s """
        if where_clause:
            where_clause = 'AND ' + where_clause
            where_clause = where_clause.replace('account_move_line', 'l1')
            query += where_clause
        query += " GROUP BY l1.id"
        self._cr.execute(query, where_params)
        for line_id, val in self._cr.fetchall():
            self.browse(line_id).balance_progressive = val

    balance_progressive = fields.Monetary(
        compute='_compute_balance_progressive',
        currency_field='company_currency_id',
        string='Progressive Balance',
        help="Field holding the progressive debit - credit of the account")
