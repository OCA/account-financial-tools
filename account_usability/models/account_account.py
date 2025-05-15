from odoo import api, fields, models


class Account(models.Model):
    _inherit = "account.account"

    group_id = fields.Many2one(search="_search_group_id")

    def _search_group_id(self, operator, value):
        if operator not in ("in", "="):
            raise NotImplementedError

        # Browse groups because value can be an odoo.tools.query.Query
        groups = self.env["account.group"].browse(value)

        if not groups:
            return [("id", "=", 0)]

        query = """
            SELECT
                a.id
            FROM
                account_account a
            JOIN
                account_group g
                ON g.code_prefix_start <= LEFT(
                    (a.code_store::json ->> %(company_id)s),
                    char_length(g.code_prefix_start)
                )
                AND g.code_prefix_end >= LEFT(
                    (a.code_store::json ->> %(company_id)s),
                    char_length(g.code_prefix_end)
                )
                AND g.company_id = %(company_id)s
            WHERE g.id IN %(group_ids)s
        """
        self.env.cr.execute(
            query,
            {
                "group_ids": tuple(groups.ids),
                "company_id": str(self.env.company.root_id.id),
            },
        )
        account_ids = [row[0] for row in self.env.cr.fetchall()]
        return [("id", "in", account_ids)]

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.mapped("group_id").invalidate_recordset()
        return res

    def write(self, vals):
        groups = self.mapped("group_id")
        res = super().write(vals)
        if "code" in vals:
            (self.mapped("group_id") | groups).invalidate_recordset()
        return res
