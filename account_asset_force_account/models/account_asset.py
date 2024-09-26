# Copyright 2024 Bernat Obrador(APSL-Nagarro)<bobrador@apsl.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    account_asset_id = fields.Many2one(
        comodel_name="account.account",
        string="Asset Account",
        compute="_compute_account_asset_id",
        help="The account used to record the value of the asset.",
    )

    account_depreciation_id = fields.Many2one(
        comodel_name="account.account",
        string="Depreciation Account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        help="The account used to record depreciation for the asset.",
        required=True,
    )

    account_expense_depreciation_id = fields.Many2one(
        comodel_name="account.account",
        string="Depreciation Expense Account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        help="The account used to record the expense of the depreciation.",
        required=True,
    )

    @api.onchange("profile_id")
    def _onchange_profile_id(self):
        # To avoid changes when the asset is confirmed
        if self.profile_id and self.state == "draft":
            self.account_depreciation_id = self.profile_id.account_depreciation_id
            self.account_expense_depreciation_id = (
                self.profile_id.account_expense_depreciation_id
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("profile_id"):
                profile = self.env["account.asset.profile"].browse(vals["profile_id"])
                if not vals.get("account_depreciation_id"):
                    vals["account_depreciation_id"] = profile.account_depreciation_id.id
                if not vals.get("account_expense_depreciation_id"):
                    vals[
                        "account_expense_depreciation_id"
                    ] = profile.account_expense_depreciation_id.id
        return super().create(vals_list)

    def _compute_account_asset_id(self):
        if len(self.account_move_line_ids.account_id) != 0:
            self.account_asset_id = self.account_move_line_ids.sorted(
                lambda line: line.create_date
            ).account_id[0]
            return
        self.account_asset_id = self.profile_id.account_asset_id
