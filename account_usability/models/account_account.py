from collections import defaultdict

from odoo import api, fields, models
from odoo.tools import SQL


class Account(models.Model):
    _inherit = "account.account"

    group_id = fields.Many2one(search="_search_group_id")

    def _search_group_id(self, operator, value):
        if operator in ("=", "in"):
            # Browse groups because value can be an odoo.tools.query.Query
            groups = self.env["account.group"].browse(value)
            mapping = self._get_group_to_accounts_mapping()
            account_ids = []
            for gid in groups.ids:
                account_ids.extend(mapping.get(gid, []))
            return [("id", "in", account_ids)]
        if operator in ("!=", "not in"):
            groups = self.env["account.group"].browse(value)
            mapping = self._get_group_to_accounts_mapping()
            account_ids = []
            for gid in groups.ids:
                account_ids.extend(mapping.get(gid, []))
            return [("id", "not in", account_ids)]
        raise NotImplementedError(
            f"Search on group_id with operator '{operator}' is not supported."
        )

    def _get_group_to_accounts_mapping(self):
        """Build a mapping of group_id -> [account_ids].

        Each account is assigned to its most specific matching group
        (longest code prefix). The mapping is cached on self.env for
        the duration of the current request to avoid repeated queries
        when multiple search calls are made (e.g. MIS report rendering).
        """
        cache_attr = "_group_to_accounts_cache"
        root_company_id = self.env.company.root_id.id
        cached = getattr(self.env.cr, cache_attr, None)
        if cached and cached.get("company_id") == root_company_id:
            return cached["mapping"]
        company_key = str(root_company_id)
        results = self.env.execute_query(
            SQL(
                """
                SELECT DISTINCT ON (aa.id)
                       aa.id AS account_id,
                       agroup.id AS group_id
                FROM account_account aa
                LEFT JOIN account_group agroup
                    ON agroup.code_prefix_start <= LEFT(
                        aa.code_store->>%(company_key)s,
                        char_length(agroup.code_prefix_start)
                    )
                    AND agroup.code_prefix_end >= LEFT(
                        aa.code_store->>%(company_key)s,
                        char_length(agroup.code_prefix_end)
                    )
                    AND agroup.company_id = %(root_company_id)s
                WHERE aa.code_store->>%(company_key)s IS NOT NULL
                ORDER BY aa.id,
                         char_length(agroup.code_prefix_start) DESC,
                         agroup.id
                """,
                company_key=company_key,
                root_company_id=root_company_id,
            )
        )
        mapping = defaultdict(list)
        for account_id, group_id in results:
            if group_id:
                mapping[group_id].append(account_id)
        setattr(
            self.env.cr,
            cache_attr,
            {
                "company_id": root_company_id,
                "mapping": mapping,
            },
        )
        return mapping

    @api.model
    def _invalidate_group_to_accounts_cache(self):
        cache_attr = "_group_to_accounts_cache"
        if hasattr(self.env.cr, cache_attr):
            delattr(self.env.cr, cache_attr)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        self._invalidate_group_to_accounts_cache()
        self.invalidate_model(["group_id"])
        self.env["account.group"].invalidate_model(["account_ids"])
        return res

    def write(self, vals):
        res = super().write(vals)
        if "code" in vals:
            self._invalidate_group_to_accounts_cache()
            self.invalidate_model(["group_id"])
            self.env["account.group"].invalidate_model(["account_ids"])
        return res
