# Copyright 2022 Tecnativa - César A. Sánchez
# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import sql

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cumulated_balance = fields.Monetary(
        string="Cumulated Balance",
        store=False,
        currency_field="company_currency_id",
        compute="_compute_cumulated_balance",
        help="Cumulated balance depending on the domain and the order chosen in the view.",
    )
    cumulated_balance_currency = fields.Monetary(
        string="Cumulated Balance in Currency",
        store=False,
        currency_field="currency_id",
        compute="_compute_cumulated_balance",
        help="Cumulated balance in currency depending on the domain and "
        "the order chosen in the view.",
    )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        def to_tuple(t):
            return tuple(map(to_tuple, t)) if isinstance(t, (list, tuple)) else t

        # Add the domain and order by in order to compute the cumulated
        # balance in _compute_cumulated_balance
        order = (order or self._order) + ", id desc"
        return super(
            AccountMoveLine, self.with_context(order_cumulated_balance=order,),
        ).search_read(domain, fields, offset, limit, order)

    @api.depends_context("order_cumulated_balance")
    def _compute_cumulated_balance(self):
        self.cumulated_balance = 0
        self.cumulated_balance_currency = 0
        order_cumulated_balance = (
            self.env.context.get("order_cumulated_balance", self._order) + ", id"
        )
        order_string = ", ".join(
            self._generate_order_by_inner(
                self._table, order_cumulated_balance, "", reverse_direction=False,
            )
        )
        query = sql.SQL(
            """SELECT account_move_line.id,
                SUM(account_move_line.balance) OVER (
                    ORDER BY {order_by_clause}
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ),
                SUM(account_move_line.amount_currency)  OVER (
                    ORDER BY {order_by_clause}
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                )
            FROM account_move_line
            LEFT JOIN account_move on account_move_line.move_id = account_move.id
            WHERE
            account_move.state = 'posted'
            """
        ).format(order_by_clause=sql.SQL(order_string),)
        self.env.cr.execute(query)
        result = {r[0]: (r[1], r[2]) for r in self.env.cr.fetchall()}
        for record in self:
            record.cumulated_balance = result[record.id][0]
            record.cumulated_balance_currency = result[record.id][1]
