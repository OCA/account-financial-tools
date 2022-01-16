# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tests.common import Form


class HrExpense(models.Model):
    _inherit = "hr.expense"

    asset_profile_id = fields.Many2one(
        comodel_name="account.asset.profile",
        string="Asset Profile",
    )

    @api.onchange("account_id")
    def _onchange_account_id(self):
        if self.account_id.asset_profile_id:
            self.asset_profile_id = self.account_id.asset_profile_id

    @api.onchange("asset_profile_id")
    def _onchange_asset_profile_id(self):
        if self.asset_profile_id.account_asset_id:
            self.account_id = self.asset_profile_id.account_asset_id

    def _expense_expand_asset_line(self, line):
        self.ensure_one()
        quantity = 1
        name = self.name
        company = self.company_id
        currency = self.currency_id
        account_date = (
            self.sheet_id.accounting_date
            or self.date
            or fields.Date.context_today(self)
        )
        taxes = self.tax_ids.with_context(round=True).compute_all(
            self.unit_amount, currency, quantity, self.product_id
        )
        amount_currency = taxes["total_excluded"]
        balance = currency._convert(
            amount_currency, company.currency_id, company, account_date
        )
        lines = []
        for i in range(1, int(self.quantity) + 1):
            cpy_line = line.copy()
            cpy_line.update(
                {
                    "name": "{} {}".format(name, i),
                    "quantity": quantity,
                    "debit": balance if balance > 0 else 0,
                    "credit": -balance if balance < 0 else 0,
                    "amount_currency": amount_currency,
                }
            )
            lines.append(cpy_line)
        return lines

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super()._get_account_move_line_values()
        for expense in self.filtered("asset_profile_id"):
            asset_lines = []
            old_asset_line = dict()
            for line in move_line_values_by_expense[expense.id]:
                if line["account_id"] == expense.asset_profile_id.account_asset_id.id:
                    line["asset_profile_id"] = expense.asset_profile_id.id
                    if expense.asset_profile_id.asset_product_item:
                        old_asset_line = line
                        asset_lines.extend(expense._expense_expand_asset_line(line))
            if asset_lines:
                if old_asset_line:
                    move_line_values_by_expense[expense.id].remove(old_asset_line)
                move_line_values_by_expense[expense.id].extend(asset_lines)
        return move_line_values_by_expense

    def action_move_create(self):
        move_group_by_sheet = super().action_move_create()
        for sheet in move_group_by_sheet:
            for move in move_group_by_sheet[sheet]:
                for aml in move.line_ids.filtered("asset_profile_id"):
                    vals = move._prepare_asset_vals(aml)
                    asset_form = Form(
                        self.env["account.asset"]
                        .with_company(move.company_id)
                        .with_context(create_asset_from_move_line=True, move_id=move.id)
                    )
                    for key, val in vals.items():
                        setattr(asset_form, key, val)
                    asset = asset_form.save()
                    asset.analytic_tag_ids = aml.analytic_tag_ids
                    aml.with_context(allow_asset=True).asset_id = asset.id
                refs = [
                    "<a href=# data-oe-model=account.asset data-oe-id=%s>%s</a>"
                    % tuple(name_get)
                    for name_get in move.line_ids.filtered(
                        "asset_profile_id"
                    ).asset_id.name_get()
                ]
                if refs:
                    message = _("This expense created the asset(s): %s") % ", ".join(
                        refs
                    )
                    move.message_post(body=message)
        return move_group_by_sheet
