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
        for move in self:
            domain = [("move_id", "=", move.id)]
            aml_groups = self.env["account.move.line"].read_group(
                domain=domain,
                fields=["balance", "account_internal_group"],
                groupby=["account_internal_group"],
                lazy=False,
            )
            move.amount_total_signed_account_internal_group_asset = sum(
                ag["balance"]
                for ag in [
                    g for g in aml_groups if g["account_internal_group"] == "asset"
                ]
            )
            move.amount_total_signed_account_internal_group_equity = sum(
                ag["balance"]
                for ag in [
                    g for g in aml_groups if g["account_internal_group"] == "equity"
                ]
            )
            move.amount_total_signed_account_internal_group_liability = sum(
                ag["balance"]
                for ag in [
                    g for g in aml_groups if g["account_internal_group"] == "liability"
                ]
            )
            move.amount_total_signed_account_internal_group_income = sum(
                ag["balance"]
                for ag in [
                    g for g in aml_groups if g["account_internal_group"] == "income"
                ]
            )
            move.amount_total_signed_account_internal_group_expense = sum(
                ag["balance"]
                for ag in [
                    g for g in aml_groups if g["account_internal_group"] == "expense"
                ]
            )
            move.amount_total_signed_account_internal_group_off_balance = sum(
                ag["balance"]
                for ag in [
                    g
                    for g in aml_groups
                    if g["account_internal_group"] == "off_balance"
                ]
            )
