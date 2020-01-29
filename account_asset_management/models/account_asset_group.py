# Copyright 2009-2018 Noviat
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAssetGroup(models.Model):
    _name = "account.asset.group"
    _description = "Asset Group"
    _order = "name"
    _parent_store = True

    name = fields.Char(string="Name", size=64, required=True, index=True)
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
    )

    @api.model
    def _default_company_id(self):
        return self.env.company
