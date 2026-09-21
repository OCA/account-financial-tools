# Copyright 2026 Acsone
# Author: Pierre Verkest <pierre.verkest@apycod.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools import SQL, Query


class AccountAccount(models.Model):
    """Extend account.account to improve code display and search
    for single-company accounts.

    In Odoo 19, code_store is company_dependent=True. When an account is linked
    to one and only one company (len(company_ids) == 1), its code for that company
    is stored in code_store_single_company. This allows account.code,
    account.display_name, and search domains by code to operate properly even when
    the session/context company differs from the account's unique company
    (such as in API requests).
    """

    _inherit = "account.account"

    code_store_single_company = fields.Char(
        string="Single Company Account Code",
        size=64,
        tracking=True,
        compute="_compute_code_store_single_company",
        store=True,
        index="trigram",
    )

    @api.depends("company_ids", "code_store")
    def _compute_code_store_single_company(self):
        for record in self:
            if len(record.company_ids) == 1:
                company = record.company_ids[0]
                record.code_store_single_company = (
                    record.sudo().with_company(company).code
                )
            else:
                record.code_store_single_company = False

    def _compute_code(self):
        res = super()._compute_code()
        for record in self:
            if not record.code and record.sudo().code_store_single_company:
                record.code = record.sudo().code_store_single_company
        return res

    def _search_code(self, operator, value):
        domain = super()._search_code(operator, value)
        return Domain.OR(
            [
                domain,
                [("code_store_single_company", operator, value)],
            ]
        )

    def _field_to_sql(
        self, alias: str, field_expr: str, query: Query | None = None
    ) -> SQL:
        if field_expr == "code":
            code_sql = super()._field_to_sql(alias, field_expr, query)
            single_company_code_sql = self._field_to_sql(
                alias, "code_store_single_company", query
            )
            return SQL("COALESCE(%s, %s)", code_sql, single_company_code_sql)
        return super()._field_to_sql(alias, field_expr, query)
