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
        # Add the significant domain in order to compute the cumulated balance in
        # _compute_cumulated_balance.
        cumulated_domain = []
        for term in domain:
            if isinstance(term, (tuple, list)) and term[0] == "move_id.state":
                # TODO: Allow multiple state conditions joined by OR
                cumulated_domain.append(("parent_state", term[1], term[2]))
            elif term[0] == "full_reconcile_id":
                cumulated_domain.append(tuple(term))
        return super(
            AccountMoveLine,
            self.with_context(domain_cumulated_balance=cumulated_domain),
        ).search_read(domain, fields, offset, limit, order)

    @api.depends_context("domain_cumulated_balance", "partner_ledger")
    def _compute_cumulated_balance(self):
        self.cumulated_balance = 0
        self.cumulated_balance_currency = 0
        query = self._where_calc(self.env.context.get("domain_cumulated_balance") or [])
        _f, where_clause, where_clause_params = query.get_sql()
        for record in self:
            query_args = where_clause_params + [
                record.account_id.id,
                record.company_id.id,
                record.date,
                record.date,
                record.id,
            ]
            # WHERE clause last line is set according order in view where this is used
            query = sql.SQL(
                """
                SELECT SUM(balance), SUM(amount_currency)
                FROM account_move_line
                WHERE {}
                    AND account_id = %s
                    AND company_id = %s
                    AND (date < %s OR (date=%s AND id <= %s))
                """
            ).format(sql.SQL(where_clause or "TRUE"))
            if self.env.context.get("partner_ledger"):
                # If showing partner ledger group by partner by default
                query_args.append(record.partner_id.id)
                query += sql.SQL("AND partner_id = %s")
            self.env.cr.execute(query, tuple(query_args))
            result = self.env.cr.fetchone()
            record.cumulated_balance = result[0]
            record.cumulated_balance_currency = result[1]
