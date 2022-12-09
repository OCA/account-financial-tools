# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    low_value = fields.Boolean(
        string="Low Value Asset",
        compute="_compute_low_value",
        search="_search_low_value",
        help="Low-Value Asset (LVA) is true when the asset profile set\n"
        "1. Asset Account = Expense (low value asset)\n"
        "2. Number of Years = 0 years\n"
        "In essense, the low value asset is not really and asset but an expense "
        "tracked as asset, as such, it has no residual value. And when removed, "
        "only status is changed (no accounting entry).",
    )

    @api.depends("profile_id", "method_number")
    def _compute_low_value(self):
        expense_account = self.env.ref("account.data_account_type_expenses")
        for asset in self:
            asset.low_value = (
                asset.profile_id.account_asset_id.user_type_id == expense_account
                and asset.method_number == 0
            )

    @api.model
    def _search_low_value(self, operator, value):
        expense_account = self.env.ref("account.data_account_type_expenses")
        if operator == "=":
            return [
                ("profile_id.account_asset_id.user_type_id", "=", expense_account.id),
                ("method_number", "=", 0),
            ]
        if operator == "!=":
            return [
                "|",
                ("profile_id.account_asset_id.user_type_id", "!=", expense_account.id),
                ("method_number", "!=", 0),
            ]

    def _compute_depreciation(self):
        res = super()._compute_depreciation()
        # For low value asset, there is no depreciation
        for asset in self:
            if asset.low_value:
                asset.value_residual = 0
        return res

    def validate(self):
        res = super().validate()
        # For low value asset, state = "open" even value_residual = 0
        for asset in self:
            if asset.low_value:
                asset.state = "open"
        return res

    def remove(self):
        self.ensure_one()
        ctx = dict(self.env.context, active_ids=self.ids, active_id=self.id)
        # Removing low value asset, use different wizard
        if self.low_value:
            view = self.env.ref("account_asset_low_value.asset_low_value_remove_form")
            return {
                "name": _("Remove Low Value Asset"),
                "view_mode": "form",
                "res_model": "account.asset.remove",
                "view_id": view.id,
                "target": "new",
                "type": "ir.actions.act_window",
                "context": ctx,
            }
        return super().remove()
