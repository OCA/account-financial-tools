# Copyright 2009-2020 Noviat
# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class AccountAssetGroup(models.Model):
    _name = "account.asset.group"
    _description = "Asset Group"
    _order = "code, name"
    _parent_store = True
    _check_company_auto = True

    name = fields.Char(size=64, required=True, index=True)
    code = fields.Char(index=True)
    parent_path = fields.Char(index=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),
    )
    parent_id = fields.Many2one(
        comodel_name="account.asset.group",
        string="Parent Asset Group",
        ondelete="restrict",
        check_company=True,
    )
    child_ids = fields.One2many(
        comodel_name="account.asset.group",
        inverse_name="parent_id",
        string="Child Asset Groups",
        check_company=True,
    )

    @api.model
    def _default_company_id(self):
        return self.env.company

    def name_get(self):
        result = []
        params = self.env.context.get("params")
        list_view = params and params.get("view_type") == "list"
        short_name_len = 16
        for rec in self:
            if rec.code:
                full_name = rec.code + " " + rec.name
                short_name = rec.code
            else:
                full_name = rec.name
                if len(full_name) > short_name_len:
                    short_name = full_name[:16] + "..."
                else:
                    short_name = full_name
            if list_view:
                name = short_name
            else:
                name = full_name
            result.append((rec.id, name))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                ("code", "=ilike", name.split(" ")[0] + "%"),
                ("name", operator, name),
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )
