# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_total_signed_account_internal_group_equity = fields.Monetary(
        compute="_compute_amount_total_signed_account_internal_group"
    )
    amount_total_signed_account_internal_group_asset = fields.Monetary(
        compute="_compute_amount_total_signed_account_internal_group"
    )
    amount_total_signed_account_internal_group_liability = fields.Monetary(
        compute="_compute_amount_total_signed_account_internal_group"
    )
    amount_total_signed_account_internal_group_income = fields.Monetary(
        compute="_compute_amount_total_signed_account_internal_group"
    )
    amount_total_signed_account_internal_group_expense = fields.Monetary(
        compute="_compute_amount_total_signed_account_internal_group"
    )
    amount_total_signed_account_internal_group_off_balance = fields.Monetary(
        compute="_compute_amount_total_signed_account_internal_group"
    )

    def _compute_amount_total_signed_account_internal_group(self):
        group_list = [
            "equity",
            "asset",
            "liability",
            "income",
            "expense",
            "off_balance",
        ]
        for move in self:
            for g in group_list:
                move[f"amount_total_signed_account_internal_group_{g}"] = 0.0
            domain = [("move_id", "=", move.id)]
            aml_groups = self.env["account.move.line"]._read_group(
                domain=domain,
                groupby=["account_internal_group"],
                aggregates=["balance:sum"],
            )
            for aml_group in aml_groups:
                acc_type = aml_group[0]  # e.g. "asset"
                balance_sum = aml_group[1]  # sum of balance
                field_name = f"amount_total_signed_account_internal_group_{acc_type}"
                if field_name in move._fields:
                    move[field_name] = balance_sum
