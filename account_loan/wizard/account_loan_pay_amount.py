# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountLoan(models.TransientModel):
    _name = "account.loan.pay.amount"
    _description = "Loan pay amount"

    loan_id = fields.Many2one(
        "account.loan",
        required=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency", related="loan_id.currency_id", readonly=True
    )
    cancel_loan = fields.Boolean(
        default=False,
    )
    date = fields.Date(required=True, default=fields.Date.today())
    amount = fields.Monetary(
        currency_field="currency_id",
        string="Amount to reduce from Principal",
    )
    fees = fields.Monetary(currency_field="currency_id", string="Bank fees")

    @api.onchange("cancel_loan")
    def _onchange_cancel_loan(self):
        if self.cancel_loan:
            self.amount = max(
                self.loan_id.line_ids.filtered(lambda r: not r.move_ids).mapped(
                    "pending_principal_amount"
                )
            )

    def new_line_vals(self, sequence):
        return {
            "loan_id": self.loan_id.id,
            "sequence": sequence,
            "payment_amount": self.amount + self.fees,
            "rate": 0,
            "interests_amount": self.fees,
            "date": self.date,
        }

    def run(self):
        self.ensure_one()
        if self.loan_id.is_leasing:
            if self.loan_id.line_ids.filtered(
                lambda r: r.date <= self.date and not r.move_ids
            ):
                raise UserError(_("Some invoices are not created"))
            if self.loan_id.line_ids.filtered(
                lambda r: r.date > self.date and r.move_ids
            ):
                raise UserError(_("Some future invoices already exists"))
        if self.loan_id.line_ids.filtered(
            lambda r: r.date < self.date and not r.move_ids
        ):
            raise UserError(_("Some moves are not created"))
        if self.loan_id.line_ids.filtered(lambda r: r.date > self.date and r.move_ids):
            raise UserError(_("Some future moves already exists"))
        lines = self.loan_id.line_ids.filtered(lambda r: r.date > self.date).sorted(
            "sequence", reverse=True
        )
        sequence = min(lines.mapped("sequence"))
        for line in lines:
            line.sequence += 1
            line.flush()
        old_line = lines.filtered(lambda r: r.sequence == sequence + 1)
        pending = old_line.pending_principal_amount
        if self.loan_id.currency_id.compare_amounts(self.amount, pending) == 1:
            raise UserError(_("Amount cannot be bigger than debt"))
        if self.loan_id.currency_id.compare_amounts(self.amount, 0) <= 0:
            raise UserError(_("Amount cannot be less than zero"))
        self.loan_id.periods += 1
        self.loan_id.fixed_periods = self.loan_id.periods - sequence
        self.loan_id.fixed_loan_amount = pending - self.amount
        new_line = self.env["account.loan.line"].create(self.new_line_vals(sequence))
        new_line.long_term_pending_principal_amount = (
            old_line.long_term_pending_principal_amount
        )
        amount = self.loan_id.loan_amount
        for line in self.loan_id.line_ids.sorted("sequence"):
            if line.move_ids:
                amount = line.final_pending_principal_amount
            else:
                line.pending_principal_amount = amount
                if line.sequence != sequence:
                    line.rate = self.loan_id.rate_period
                    line.check_amount()
                amount -= line.payment_amount - line.interests_amount
        if self.loan_id.long_term_loan_account_id:
            self.loan_id.check_long_term_principal_amount()
        if self.loan_id.currency_id.compare_amounts(pending, self.amount) == 0:
            self.loan_id.write({"state": "cancelled"})
        return new_line.view_process_values()
