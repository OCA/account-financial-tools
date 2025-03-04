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
        store=True,
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
            self._compute_account_asset_id()

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

    @api.depends("account_move_line_ids", "profile_id")
    def _compute_account_asset_id(self):
        for record in self:
            # Cannot update the account_asset_id if the asset is not in draft state
            if record.state != "draft":
                continue
            # Looks if the asset comes from an invoice, if so, takes the account from the invoice
            if len(record.account_move_line_ids.account_id) != 0:
                invoice_line = record.account_move_line_ids.filtered(
                    lambda line: line.move_id.move_type == "in_invoice"
                )
                if invoice_line:
                    record.account_asset_id = invoice_line.account_id
                    continue
            # If not, takes the account from the profile
            record.account_asset_id = record.profile_id.account_asset_id
