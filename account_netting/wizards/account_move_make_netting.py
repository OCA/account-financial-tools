# Copyright 2015 Pedro M. Baeza
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, exceptions, fields, models


class AccountMoveMakeNetting(models.TransientModel):
    _name = "account.move.make.netting"
    _description = "Wizard to generate account moves for netting"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        required=True,
        domain="[('type', '=', 'general')]",
    )
    move_line_ids = fields.Many2many(comodel_name="account.move.line",)
    balance = fields.Float(readonly=True,)
    balance_type = fields.Selection(
        selection=[("pay", "To pay"), ("receive", "To receive")], readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        if len(self.env.context.get("active_ids", [])) < 2:
            raise exceptions.ValidationError(
                _("You should compensate at least 2 journal entries.")
            )
        move_lines = self.env["account.move.line"].browse(
            self.env.context["active_ids"]
        )
        if any(
            x not in ("payable", "receivable")
            for x in move_lines.mapped("account_id.user_type_id.type")
        ):
            raise exceptions.ValidationError(
                _("All entries must have a receivable or payable account")
            )
        if any(move_lines.mapped("reconciled")):
            raise exceptions.ValidationError(_("All entries mustn't been reconciled"))
        if len(move_lines.mapped("account_id")) == 1:
            raise exceptions.ValidationError(
                _(
                    "The 'Compensate' function is intended to balance "
                    "operations on different accounts for the same partner.\n"
                    "In this case all selected entries belong to the same "
                    "account.\n Please use the 'Reconcile' function."
                )
            )
        if len(move_lines.mapped("partner_id")) != 1:
            raise exceptions.ValidationError(
                _(
                    "All entries should have a partner and the partner must "
                    "be the same for all."
                )
            )
        res = super().default_get(fields_list)
        res["move_line_ids"] = [(6, 0, move_lines.ids)]
        debit_move_lines_debit = move_lines.filtered("debit")
        credit_move_lines_debit = move_lines.filtered("credit")
        balance = abs(sum(debit_move_lines_debit.mapped("amount_residual"))) - abs(
            sum(credit_move_lines_debit.mapped("amount_residual"))
        )
        res["balance"] = abs(balance)
        res["balance_type"] = "pay" if balance < 0 else "receive"
        return res

    def button_compensate(self):
        self.ensure_one()
        # Create account move
        move = self.env["account.move"].create(
            {"ref": _("AR/AP netting"), "journal_id": self.journal_id.id}
        )
        # Group amounts by account
        account_groups = self.move_line_ids.read_group(
            [("id", "in", self.move_line_ids.ids)],
            ["account_id", "amount_residual"],
            ["account_id"],
        )
        debtors = []
        creditors = []
        total_debtors = 0
        total_creditors = 0
        for account_group in account_groups:
            balance = account_group["amount_residual"]
            group_vals = {
                "account_id": account_group["account_id"][0],
                "balance": abs(balance),
            }
            if balance > 0:
                debtors.append(group_vals)
                total_debtors += balance
            else:
                creditors.append(group_vals)
                total_creditors += abs(balance)
        # Create move lines
        netting_amount = min(total_creditors, total_debtors)
        field_map = {1: "debit", 0: "credit"}
        move_lines = []
        for i, group in enumerate([debtors, creditors]):
            available_amount = netting_amount
            for account_group in group:
                if account_group["balance"] > available_amount:
                    amount = available_amount
                else:
                    amount = account_group["balance"]
                move_line_vals = {
                    field_map[i]: amount,
                    "partner_id": self.move_line_ids[0].partner_id.id,
                    "name": move.ref,
                    "account_id": account_group["account_id"],
                }
                move_lines.append((0, 0, move_line_vals))
                available_amount -= account_group["balance"]
                if available_amount <= 0:
                    break
        if move_lines:
            move.write({"line_ids": move_lines})
        # Make reconciliation
        for move_line in move.line_ids:
            to_reconcile = move_line + self.move_line_ids.filtered(
                lambda x: x.account_id == move_line.account_id
            )
            to_reconcile.reconcile()
        # Open created move
        action = self.env.ref("account.action_move_journal_line").read()[0]
        action["view_mode"] = "form"
        del action["views"]
        del action["view_id"]
        action["res_id"] = move.id
        return action
