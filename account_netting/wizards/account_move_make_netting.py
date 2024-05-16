# Copyright 2015 Pedro M. Baeza
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveMakeNetting(models.TransientModel):
    _name = "account.move.make.netting"
    _description = "Wizard to generate account moves for netting"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True)
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        check_company=True,
    )
    move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        check_company=True,
        string="Journal Items to Compensate",
    )
    partner_id = fields.Many2one("res.partner", readonly=True)
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    balance = fields.Monetary(readonly=True, currency_field="company_currency_id")
    balance_type = fields.Selection(
        selection=[("pay", "To pay"), ("receive", "To receive")],
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        if len(self.env.context.get("active_ids", [])) < 2:
            raise UserError(_("You should select at least 2 journal items."))
        move_lines = self.env["account.move.line"].browse(
            self.env.context["active_ids"]
        )
        partners = self.env["res.partner"]
        for line in move_lines:
            if line.parent_state != "posted":
                raise UserError(_("Line '%s' is not posted.") % line.display_name)
            if line.account_id.account_type not in (
                "liability_payable",
                "asset_receivable",
            ):
                raise UserError(
                    _(
                        "Line '%(line)s' has account '%(account)s' which is not "
                        "a payable nor a receivable account."
                    )
                    % {
                        "line": line.display_name,
                        "account": line.account_id.display_name,
                    }
                )
            if line.reconciled:
                raise UserError(
                    _("Line '%s' is already reconciled.") % line.display_name
                )
            if not line.partner_id:
                raise UserError(
                    _("Line '%s' doesn't have a partner.") % line.display_name
                )
            partners |= line.partner_id

        if len(move_lines.account_id) == 1:
            raise UserError(
                _(
                    "The 'Compensate' function is intended to balance "
                    "operations on different accounts for the same partner. "
                    "The selected journal items have the same "
                    "account '%s', so you should use the 'Reconcile' function instead."
                )
                % move_lines.account_id.display_name
            )
        if len(partners) != 1:
            raise UserError(
                _(
                    "The selected journal items have different partners: %s. "
                    "All the selected journal items must have the same partner."
                )
                % ", ".join([p.display_name for p in partners])
            )
        res = super().default_get(fields_list)
        company = self.env.company
        ccur = company.currency_id
        debit_move_lines_debit = move_lines.filtered("debit")
        credit_move_lines_debit = move_lines.filtered("credit")
        balance = ccur.round(
            abs(sum(debit_move_lines_debit.mapped("amount_residual")))
            - abs(sum(credit_move_lines_debit.mapped("amount_residual")))
        )
        res.update(
            {
                "balance": abs(balance),
                "balance_type": "pay"
                if ccur.compare_amounts(balance, 0) < 0
                else "receive",
                "company_id": company.id,
                "move_line_ids": move_lines.ids,
                "partner_id": partners.id,
            }
        )
        return res

    def _prepare_account_move(self):
        # Group amounts by account
        account_groups = self.move_line_ids.read_group(
            [("id", "in", self.move_line_ids.ids)],
            ["account_id", "amount_residual"],
            ["account_id"],
        )
        debtors = []
        creditors = []
        total_debtors = 0.0
        total_creditors = 0.0
        ccur = self.company_id.currency_id
        for account_group in account_groups:
            balance = account_group["amount_residual"]
            group_vals = {
                "account_id": account_group["account_id"][0],
                "balance": abs(balance),
            }
            if ccur.compare_amounts(balance, 0) > 0:
                debtors.append(group_vals)
                total_debtors += balance
            else:
                creditors.append(group_vals)
                total_creditors += abs(balance)
        # Compute move lines
        netting_amount = min(total_creditors, total_debtors)
        field_map = {1: "debit", 0: "credit"}
        move_lines = []
        for i, group in enumerate([debtors, creditors]):
            available_amount = netting_amount
            for account_group in group:
                move_line_vals = {
                    field_map[i]: min(available_amount, account_group["balance"]),
                    "partner_id": self.partner_id.id,
                    "account_id": account_group["account_id"],
                }
                move_lines.append((0, 0, move_line_vals))
                available_amount -= account_group["balance"]
                if ccur.compare_amounts(available_amount, 0) <= 0:
                    break
        vals = {
            "ref": _("AR/AP netting"),
            "journal_id": self.journal_id.id,
            "company_id": self.company_id.id,
            "line_ids": move_lines,
        }
        return vals

    def button_compensate(self):
        self.ensure_one()
        # Create account move
        move = self.env["account.move"].create(self._prepare_account_move())
        move.action_post()
        # Make reconciliation
        for move_line in move.line_ids:
            to_reconcile = move_line + self.move_line_ids.filtered(
                lambda x, move_line=move_line: x.account_id == move_line.account_id
            )
            to_reconcile.reconcile()
        # Open created move
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_journal_line"
        )
        action.update(
            {
                "view_mode": "form",
                "views": False,
                "view_id": False,
                "res_id": move.id,
            }
        )
        return action
