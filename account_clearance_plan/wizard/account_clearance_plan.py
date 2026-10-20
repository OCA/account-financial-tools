# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountClearancePlanLine(models.TransientModel):
    _name = "account.clearance.plan.line"
    _description = "Clearance Plan Line"

    name = fields.Char(
        string="Label",
        required=True,
        default=lambda self: self.env.company.clearance_plan_move_line_name,
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
                raise ValidationError(_("Amounts should all be positive."))


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
    amount_unallocated = fields.Float(compute="_compute_amount_unallocated")
    clearance_plan_line_ids = fields.One2many(
        comodel_name="account.clearance.plan.line", inverse_name="clearance_plan_id"
    )
    mode = fields.Selection(
        [("receivable", "Receivable"), ("payable", "Payable")],
        help="Receivable if we clear customers debts, payable if own debts.",
    )

    @api.depends("clearance_plan_line_ids.amount", "amount_to_allocate")
    def _compute_amount_unallocated(self):
        for rec in self:
            rec.amount_unallocated = rec.amount_to_allocate - sum(
                rec.clearance_plan_line_ids.mapped("amount")
            )

    def _get_move_lines_from_context(self):
        active_model = self._context.get("active_model")
        if active_model == "account.move":
            move_line_ids = []
            for move in self.env["account.move"].browse(
                self._context.get("active_ids")
            ):
                move_line_ids += move._get_open_move_lines_ids()
        elif active_model != "account.move.line":
            raise UserError(
                _(
                    "Programming error: wizard action executed with 'active_model' "
                    "different from 'account.move.line' in context."
                )
            )
        else:
            move_line_ids = self._context.get("active_ids")

        return self.env["account.move.line"].browse(move_line_ids)

    @api.model
    def default_get(self, fields_list):
        rec = super().default_get(fields_list)

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
        # Check account is of type 'receivable' or 'payable'
        if account_id.account_type not in ("asset_receivable", "liability_payable"):
            raise UserError(
                _(
                    "Please select items from an account "
                    "of type 'receivable' or 'payable'."
                )
            )

        rec.update(
            {
                "journal_id": self.env.company.clearance_plan_journal_id.id,
                "amount_to_allocate": abs(total_amount_residual),
                "mode": "receivable" if total_amount_residual > 0 else "payable",
                "move_line_ids": move_lines.ids,
                "account_id": account_id.id,
                "partner_id": partner_id.id,
            }
        )

        return rec

    def _create_reverse_amount_residual_lines(self, move):
        new_lines = self.env["account.move.line"]
        for line in self.move_line_ids:
            vals = line.copy_data()[0]
            vals.update(
                {
                    "move_id": move.id,
                    "balance": -line.amount_residual,
                    "amount_currency": -line.amount_residual_currency,
                    "name": _("Clearance Plan: ") + (vals.get("name") or ""),
                }
            )
            new_line = (
                self.env["account.move.line"]
                .with_context(check_move_validity=False)
                .create(vals)
            )
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

    def _get_move_vals(self):
        return {
            "journal_id": self.journal_id.id,
            "ref": self.move_ref,
            "narration": self.move_narration,
            "partner_id": self.partner_id.id,
        }

    def confirm_plan(self):
        self.ensure_one()
        if self.amount_unallocated != 0:
            raise UserError(_("%s still to allocate.") % self.amount_unallocated)

        move = self.env["account.move"].create(self._get_move_vals())
        reversed_lines = self._create_reverse_amount_residual_lines(move)
        self._create_clearance_move_lines(move)

        move.action_post()
        (self.move_line_ids | reversed_lines).reconcile()

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "context": self.env.context,
        }
