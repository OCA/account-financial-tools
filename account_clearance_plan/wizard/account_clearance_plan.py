# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountClearancePlanLine(models.TransientModel):
    _name = "account.clearance.plan.line"
    _description = "Clearance Plan Line"

    name = fields.Char(
        string="Label",
        required=True,
        default=lambda self:
            self.env.user.company_id.clearance_plan_move_line_name,
    )
    clearance_plan_id = fields.Many2one(
        comodel_name="account.clearance.plan", required=True
    )
    amount = fields.Float(required=True)
    date_maturity = fields.Date(string="Due Date", required=True)

    @api.constrains("amount")
    def _check_positive_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise Warning(_("Amounts should all be positive."))


class AccountClearancePlan(models.TransientModel):
    _name = "account.clearance.plan"
    _description = "Clearance Plan"

    account_id = fields.Many2one("account.account", readonly=True)
    partner_id = fields.Many2one("res.partner", readonly=True)
    move_line_ids = fields.Many2many("account.move.line", readonly=True)
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        required=True,
        help="Journal of the new entry.",
    )
    move_ref = fields.Char(
        string="Journal Entry Reference",
        help="Reference of the new journal entry that will be generated.",
    )
    move_narration = fields.Text(
        string="Journal Entry Internal Note",
        help="Internal note of the new journal entry that will be generated.",
    )
    amount_to_allocate = fields.Float(string="Total Amount to Allocate", readonly=True)
    amount_unallocated = fields.Float(
        string="Amount Unallocated", compute="_compute_amount_unallocated"
    )
    clearance_plan_line_ids = fields.One2many(
        comodel_name="account.clearance.plan.line", inverse_name="clearance_plan_id"
    )
    exigible_on_payment = fields.Boolean()
    mode = fields.Selection(
        [("receivable", "Receivable"), ("payable", "Payable")],
        help="Receivable if we clear customers debts, payable if own debts.",
    )

    @api.depends("clearance_plan_line_ids")
    def _compute_amount_unallocated(self):
        for rec in self:
            rec.amount_unallocated = rec.amount_to_allocate - sum(
                rec.clearance_plan_line_ids.mapped("amount")
            )

    def _get_move_lines_from_context(self):
        active_model = self._context.get("active_model")
        if active_model == "account.invoice":
            move_line_ids = []
            for invoice in self.env["account.invoice"].browse(
                self._context.get("active_ids")
            ):
                move_line_ids += invoice._get_open_move_lines_ids()
        elif not self._context.get("active_model") == "account.move.line":
            raise UserError(
                _(
                    "Programming error: wizard action executed with 'active_model' "
                    "different from 'account.move.line' in context."
                )
            )
        else:
            move_line_ids = self._context.get("active_ids")
            if "on_payment" in self.env["account.move.line"].browse(
                move_line_ids
            ).mapped("move_id.line_ids.tax_ids.tax_exigibility"):
                raise UserError(
                    _(
                        "Please select only items not on entries "
                        "with taxes eligible on payment."
                    )
                )

        return self.env["account.move.line"].browse(move_line_ids)

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)

        move_lines = self._get_move_lines_from_context()
        account_id = move_lines.mapped("account_id")
        partner_id = move_lines.mapped("partner_id")
        total_amount_residual = sum(move_lines.mapped("amount_residual"))

        # Check all move lines are from same partner
        if len(partner_id.ids) != 1:
            raise UserError(_("Please select items from exactly one partner."))
        # Check all move lines are from same account
        if len(account_id.ids) != 1:
            raise UserError(_("Please select items from exactly one account."))
        # Check account is of type type is 'receivable' or 'payable'
        if account_id.user_type_id.type not in ("receivable", "payable"):
            raise UserError(
                _(
                    "Please select items from an account "
                    "of type 'receivable' or 'payable'."
                )
            )
        # If move_lines are linked to ml with on_payment taxes treatment differs
        exigible_on_payment = "on_payment" in move_lines.mapped(
            "move_id.line_ids.tax_ids.tax_exigibility"
        )
        if exigible_on_payment:
            move_lines = move_lines.mapped("move_id.line_ids")
            # Check technical account is set in configs
            if not self.env.user.company_id.clearance_plan_technical_account_id:
                raise UserError(
                    _(
                        "If you select items with taxes exigible "
                        "based on payment, please "
                        "configure a technical account in 'Settings'."
                    )
                )
            # Check all move lines are fully open
            # Note: This is a limitation to ease further computation
            if move_lines.mapped("matched_debit_ids") or move_lines.mapped(
                "matched_credit_ids"
            ):
                raise UserError(
                    _(
                        "If you select items with taxes exigible based on "
                        "payment, please select only fully open ones."
                    )
                )

        rec.update(
            {
                "journal_id": self.env.user.company_id.clearance_plan_journal_id.id,
                "amount_to_allocate": abs(total_amount_residual),
                "mode": "receivable" if total_amount_residual > 0 else "payable",
                "move_line_ids": move_lines.ids,
                "account_id": account_id.id,
                "partner_id": partner_id.id,
                "exigible_on_payment": exigible_on_payment,
            }
        )

        return rec

    def _create_move(self):
        return self.env["account.move"].create(
            {
                "journal_id": self.journal_id.id,
                "ref": self.move_ref,
                "narration": self.move_narration,
            }
        )

    def _create_reversed_move(self, move_lines):
        reversed_move = self._create_move()
        tax_lines = move_lines.filtered("tax_line_id")
        lines_with_taxes = move_lines.filtered("tax_ids")
        remaining_lines = move_lines - lines_with_taxes - tax_lines

        # group and reverse remaining_lines (i.e. payable/receivable lines)
        reversed_lines = self._create_reversed_lines(reversed_move, remaining_lines)
        # group and reverse tax_lines
        self._create_tax_lines(reversed_move, tax_lines, reverse=True)
        # group and reverse lines_with_taxes
        self._create_lines_with_taxes(reversed_move, lines_with_taxes, reverse=True)

        # Assert balance once all mv_line created
        reversed_move.assert_balanced()
        reversed_move.action_post()
        (remaining_lines | reversed_lines).reconcile()

    def _create_new_move(self):
        move = self._create_move()
        tax_lines = self.move_line_ids.filtered("tax_line_id")
        lines_with_taxes = self.move_line_ids.filtered("tax_ids")
        self._create_clearance_move_lines(move)
        self._create_tax_lines(move, tax_lines)
        self._create_lines_with_taxes(move, lines_with_taxes)

        # Assert balance once all mv_line created
        move.assert_balanced()
        move.action_post()
        return move

    def confirm_plan(self):
        self.ensure_one()
        if self.amount_unallocated != 0:
            raise UserError(_("%s still to allocate.") % self.amount_unallocated)

        if self.exigible_on_payment:
            for invoice in self.move_line_ids.mapped("invoice_id"):
                move_lines = self.move_line_ids.filtered(
                    lambda l: l.invoice_id == invoice
                )
                self._create_reversed_move(move_lines)
            move = self._create_new_move()
        else:
            move = self._create_move()
            reversed_lines = self._create_reverse_amount_residual_lines(move)
            self._create_clearance_move_lines(move)

            # Assert balance once all mv_line created
            move.assert_balanced()
            move.action_post()
            (self.move_line_ids | reversed_lines).reconcile()

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "context": self.env.context,
        }

    #############################
    # Create move lines helpers #
    #############################

    def _create_reverse_amount_residual_lines(self, move):
        new_lines = self.env["account.move.line"]
        for line in self.move_line_ids:
            new_line = line.with_context(check_move_validity=False).copy(
                default={
                    "move_id": move.id,
                    "debit": abs(line.amount_residual) if line.credit > 0 else 0,
                    "credit": abs(line.amount_residual) if line.debit > 0 else 0,
                    "invoice_id": False,
                }
            )
            new_line.write({"name": (_("Clearance Plan: ") + new_line.name)})
            new_lines |= new_line
        return new_lines

    def _get_move_line_vals(self, move, line):
        return {
            "move_id": move.id,
            "debit": line.amount if self.mode == "receivable" else 0,
            "credit": line.amount if self.mode == "payable" else 0,
            "date_maturity": line.date_maturity,
            "name": line.name,
            "account_id": self.account_id.id,
            "partner_id": self.partner_id.id,
        }

    def _create_clearance_move_lines(self, move):
        self.ensure_one()
        for line in self.clearance_plan_line_ids:
            self.env["account.move.line"].with_context(
                check_move_validity=False
            ).create(self._get_move_line_vals(move, line))

    def _create_reversed_lines(self, move, move_lines):
        new_lines = self.env["account.move.line"]
        for group in self.env["account.move.line"].read_group(
            domain=[["id", "in", move_lines.ids]],
            fields=["balance:sum"],
            groupby=["account_id"],
        ):
            new_line = self.env["account.move.line"].with_context(
                check_move_validity=False
            ).create(
                {
                    "move_id": move.id,
                    "debit": abs(group["balance"]) if group["balance"] < 0 else 0,
                    "credit": group["balance"] if group["balance"] > 0 else 0,
                    "partner_id": self.partner_id.id,
                    "account_id": group["account_id"][0],
                }
            )
            new_lines |= new_line
        return new_lines

    def _create_tax_lines(self, move, move_lines, reverse=False):
        for group in self.env["account.move.line"].read_group(
            domain=[["id", "in", move_lines.ids]],
            fields=["balance:sum"],
            groupby=["tax_line_id", "account_id"],
            lazy=False,
        ):
            if group["tax_line_id"]:
                debit = group["balance"] if group["balance"] > 0 else 0
                credit = abs(group["balance"]) if group["balance"] < 0 else 0
                if reverse:
                    debit, credit = credit, debit
                self.env["account.move.line"].with_context(
                    check_move_validity=False
                ).create(
                    {
                        "move_id": move.id,
                        "debit": debit,
                        "credit": credit,
                        "partner_id": self.partner_id.id,
                        "account_id": group["account_id"][0],
                        "tax_line_id": group["tax_line_id"][0],
                        "name": self.env["account.tax"]
                        .browse(group["tax_line_id"][0])
                        .name,
                    }
                )

    def _create_lines_with_taxes(self, move, move_lines, reverse=False):
        technical_account_id = (
            self.env.user.company_id.clearance_plan_technical_account_id.id
        )
        groups = defaultdict(float)
        for line in move_lines:
            groups[line.tax_ids] += line.balance
        for tax_ids, balance in groups.items():
            debit = balance if balance > 0 else 0
            credit = abs(balance) if balance < 0 else 0
            if reverse:
                debit, credit = credit, debit
            self.env["account.move.line"].with_context(
                check_move_validity=False
            ).create(
                {
                    "move_id": move.id,
                    "debit": debit,
                    "credit": credit,
                    "partner_id": self.partner_id.id,
                    "account_id": technical_account_id,
                    "tax_ids": [(6, 0, tax_ids.ids)],
                    "name": self.env["account.account"]
                    .browse(technical_account_id)
                    .name,
                }
            )
