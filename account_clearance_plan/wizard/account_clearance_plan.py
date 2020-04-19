# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountClearancePlanLine(models.TransientModel):
    _name = "account.clearance.plan.line"
    _description = "Clearance Plan Line"

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
    amount_allocated = fields.Float(
        string="Amount Allocated", compute="_compute_amount_allocated"
    )
    clearance_plan_line_ids = fields.One2many(
        comodel_name="account.clearance.plan.line", inverse_name="clearance_plan_id"
    )

    @api.onchange("clearance_plan_line_ids")
    def _compute_amount_allocated(self):
        for rec in self:
            rec.amount_allocated = sum(rec.clearance_plan_line_ids.mapped("amount"))

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)

        if not self._context.get("active_model") == "account.move.line":
            raise UserError(
                _(
                    "Programming error: wizard action executed with 'active_model' "
                    "different from 'account.move.line' in context."
                )
            )

        move_lines = self.env["account.move.line"].browse(
            self._context.get("active_ids")
        )
        account_id = move_lines.mapped("account_id")

        # Check all move lines are from same partner
        if len(move_lines.mapped("partner_id").ids) != 1:
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

        rec.update(
            {
                "journal_id": self.env.user.company_id.clearance_plan_journal_id.id,
                "amount_to_allocate": abs(sum(move_lines.mapped("amount_residual"))),
                "move_line_ids": move_lines.ids,
            }
        )

        return rec

    def _create_reverse_amount_residual_lines(self, move):
        new_lines = self.env["account.move.line"]
        for line in self.move_line_ids:
            new_line = line.with_context(check_move_validity=False).copy(
                default={
                    "move_id": move.id,
                    "debit": abs(line.amount_residual) if line.credit > 0 else 0,
                    "credit": abs(line.amount_residual) if line.debit > 0 else 0,
                }
            )
            new_line.write({"name": (_("Clearance Plan: ") + new_line.name)})
            new_lines |= new_line
        return new_lines

    def _create_clearance_move_lines(self, move):
        account_id = self.move_line_ids.mapped("account_id")
        partner_id = self.move_line_ids.mapped("partner_id")
        move_line_name = self.env.user.company_id.clearance_plan_move_line_name
        negative_amount_residual = sum(move.line_ids.mapped("amount_residual")) < 0
        for line in self.clearance_plan_line_ids:
            self.env["account.move.line"].with_context(
                check_move_validity=False
            ).create(
                {
                    "move_id": move.id,
                    "debit": line.amount if negative_amount_residual else 0,
                    "credit": line.amount if not negative_amount_residual else 0,
                    "date_maturity": line.date_maturity,
                    "name": move_line_name,
                    "account_id": account_id.id,
                    "partner_id": partner_id.id,
                }
            )

    def confirm_plan(self):
        self.ensure_one()
        if self.amount_to_allocate != self.amount_allocated:
            raise UserError(
                _("Amount to allocate and amount allocated must be equals.")
            )

        move = self.env["account.move"].create(
            {
                "journal_id": self.journal_id.id,
                "ref": self.move_ref,
                "narration": self.move_narration,
            }
        )
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
