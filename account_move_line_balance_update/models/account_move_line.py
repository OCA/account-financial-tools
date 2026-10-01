# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _is_balance_update_counterpart(self, line):
        self.ensure_one()
        same_account = self.env.context.get("force_same_counterpart_account", False)
        company_currency = self.company_currency_id
        return (
            line.display_type == self.display_type
            and line.company_id == self.company_id
            and (not same_account or line.account_id == self.account_id)
            and line.currency_id == self.currency_id
            and company_currency.compare_amounts(line.debit, self.credit) == 0
            and company_currency.compare_amounts(line.credit, self.debit) == 0
            and line.currency_id.compare_amounts(
                line.amount_currency, -self.amount_currency
            )
            == 0
        )

    def _get_balance_update_counterpart_line(self):
        self.ensure_one()
        return self.move_id.line_ids.filtered(
            lambda line: line != self and self._is_balance_update_counterpart(line)
        )

    def _check_balance_update_counterpart_line(self):
        self.ensure_one()
        counterpart_line = self._get_balance_update_counterpart_line()
        if not counterpart_line:
            raise UserError(
                _(
                    "The operation cannot be performed because no counterpart journal "
                    "item was found in the same journal entry."
                )
            )
        if len(counterpart_line) > 1:
            raise UserError(
                _(
                    "The operation cannot be performed because more than one matching "
                    "counterpart journal item was found."
                )
            )
        return counterpart_line

    def action_open_balance_update_wizard(self):
        if len(self) != 1:
            raise UserError(_("Select a single journal item."))
        self.ensure_one()
        counterpart_line = self._check_balance_update_counterpart_line()
        return {
            "name": _("Modify balance"),
            "type": "ir.actions.act_window",
            "res_model": "account.move.line.balance.update.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "account_move_line_balance_update."
                "view_account_move_line_balance_update_wizard_form"
            ).id,
            "target": "new",
            "context": {
                "default_line_id": self.id,
                "default_counterpart_line_id": counterpart_line.id,
                "default_new_balance": self.balance,
                "default_new_amount_currency": self.amount_currency,
            },
        }
