# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveLineBalanceUpdateWizard(models.TransientModel):
    _name = "account.move.line.balance.update.wizard"
    _description = "Modify Journal Item Balance"

    line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Journal Item",
        required=True,
        readonly=True,
    )
    counterpart_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Counterpart Journal Item",
        required=True,
        readonly=True,
    )
    currency_id = fields.Many2one(related="line_id.company_currency_id")
    line_currency_id = fields.Many2one(related="line_id.currency_id")
    has_foreign_currency = fields.Boolean(
        compute="_compute_has_foreign_currency",
    )
    current_balance = fields.Monetary(
        string="Current Balance",
        related="line_id.balance",
        currency_field="currency_id",
    )
    counterpart_current_balance = fields.Monetary(
        string="Counterpart Current Balance",
        related="counterpart_line_id.balance",
        currency_field="currency_id",
    )
    current_amount_currency = fields.Monetary(
        string="Current Amount in Currency",
        related="line_id.amount_currency",
        currency_field="line_currency_id",
    )
    counterpart_current_amount_currency = fields.Monetary(
        string="Counterpart Current Amount in Currency",
        related="counterpart_line_id.amount_currency",
        currency_field="line_currency_id",
    )
    new_balance = fields.Monetary(
        currency_field="currency_id",
    )
    new_amount_currency = fields.Monetary(
        string="New Amount in Currency",
        currency_field="line_currency_id",
    )

    @api.depends("currency_id", "line_currency_id")
    def _compute_has_foreign_currency(self):
        for wizard in self:
            wizard.has_foreign_currency = (
                wizard.line_currency_id
                and wizard.currency_id
                and wizard.line_currency_id != wizard.currency_id
            )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        line = self.env["account.move.line"].browse(values.get("line_id"))
        if line:
            if "new_balance" in fields_list and "new_balance" not in values:
                values["new_balance"] = line.balance
            if (
                "new_amount_currency" in fields_list
                and "new_amount_currency" not in values
            ):
                values["new_amount_currency"] = line.amount_currency
            if (
                "counterpart_line_id" in fields_list
                and "counterpart_line_id" not in values
            ):
                counterpart_line = line._get_balance_update_counterpart_line()
                values["counterpart_line_id"] = counterpart_line[:1].id
        return values

    def _prepare_debit_credit_vals(self, line, balance):
        balance = line.company_currency_id.round(balance)
        if line.company_currency_id.compare_amounts(balance, 0.0) >= 0:
            return {
                "debit": balance,
                "credit": 0.0,
            }
        return {
            "debit": 0.0,
            "credit": -balance,
        }

    def _check_counterpart_line(self):
        self.ensure_one()
        counterpart_line = self.line_id._check_balance_update_counterpart_line()
        if self.counterpart_line_id != counterpart_line:
            raise UserError(
                _(
                    "The operation cannot be performed because no counterpart journal "
                    "item was found in the same journal entry."
                )
            )

    def _prepare_update_vals(self, line, balance, amount_currency):
        if self.has_foreign_currency:
            return {"amount_currency": line.currency_id.round(amount_currency)}
        return self._prepare_debit_credit_vals(line, balance)

    def _write_balances(self):
        self.ensure_one()
        self._check_counterpart_line()
        self.line_id.move_id.write(
            {
                "line_ids": [
                    Command.update(
                        self.line_id.id,
                        self._prepare_update_vals(
                            self.line_id,
                            self.new_balance,
                            self.new_amount_currency,
                        ),
                    ),
                    Command.update(
                        self.counterpart_line_id.id,
                        self._prepare_update_vals(
                            self.counterpart_line_id,
                            -self.new_balance,
                            -self.new_amount_currency,
                        ),
                    ),
                ]
            }
        )

    def action_apply(self):
        self.ensure_one()
        self._check_counterpart_line()
        move = self.line_id.move_id
        if move.state == "posted":
            move.button_draft()
            self._write_balances()
            move.action_post()
        else:
            self._write_balances()
        return {"type": "ir.actions.act_window_close"}
