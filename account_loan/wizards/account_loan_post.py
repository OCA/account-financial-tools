# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountLoanPost(models.TransientModel):
    _name = "account.loan.post"
    _description = "Loan post"

    @api.model
    def _default_journal_id(self):
        loan_id = self.env.context.get("default_loan_id")
        if loan_id:
            return self.env["account.loan"].browse(loan_id).journal_id.id

    @api.model
    def _default_account_id(self):
        loan_id = self.env.context.get("default_loan_id")
        if loan_id:
            loan = self.env["account.loan"].browse(loan_id)
            if loan.is_leasing:
                return loan.leased_asset_account_id.id
            else:
                return loan.partner_id.with_company(
                    loan.company_id
                ).property_account_receivable_id.id

    loan_id = fields.Many2one(
        "account.loan",
        required=True,
        readonly=True,
    )
    journal_id = fields.Many2one(
        "account.journal", required=True, default=lambda r: r._default_journal_id()
    )
    account_id = fields.Many2one(
        "account.account", required=True, default=lambda r: r._default_account_id()
    )

    def move_line_vals(self):
        res = list()
        partner = self.loan_id.partner_id.with_company(self.loan_id.company_id)
        line = self.loan_id.line_ids.filtered(lambda r: r.sequence == 1)
        # Amounts are evaled if > 0 for allowing negative loans to be able to be the
        # donors of the loan
        loan_currency_amount = self.loan_id.currency_id._convert(
            from_amount=line.pending_principal_amount,
            to_currency=self.loan_id.company_id.currency_id,
            company=self.loan_id.company_id,
            date=self.loan_id.start_date,
            round=True,
        )
        res.append(
            {
                "account_id": self.account_id.id,
                "name": self.loan_id.name,
                "partner_id": partner.id,
                "credit": -loan_currency_amount if loan_currency_amount < 0 else 0,
                "debit": loan_currency_amount if loan_currency_amount > 0 else 0,
                "credit": 0,
                "currency_id": self.loan_id.currency_id.id,
                "amount_currency": line.pending_principal_amount,
            }
        )
        diff_amount = abs(line.pending_principal_amount) - abs(
            line.long_term_pending_principal_amount
        )
        if diff_amount > 0:
            loan_currency_diff_amount =  self.loan_id.currency_id._convert(
                from_amount=diff_amount,
                to_currency=self.loan_id.company_id.currency_id,
                company=self.loan_id.company_id,
                date=self.loan_id.start_date,
                round=True,
            )
            res.append(
                {
                    "account_id": self.loan_id.short_term_loan_account_id.id,
                    "credit": loan_currency_diff_amount if loan_currency_amount > 0 else 0,
                    "debit": loan_currency_diff_amount if loan_currency_amount < 0 else 0,
                    "currency_id": self.loan_id.currency_id.id,
                    "amount_currency": -1 * diff_amount if loan_currency_amount > 0 else diff_amount,
                }
            )
        diff_amount = abs(line.long_term_pending_principal_amount)
        if diff_amount > 0 and self.loan_id.long_term_loan_account_id:
            laon_currency_diff_amount = self.loan_id.currency_id._convert(
                from_amount=diff_amount,
                to_currency=self.loan_id.company_id.currency_id,
                company=self.loan_id.company_id,
                date=self.loan_id.start_date,
                round=True,
            )
            res.append(
                {
                    "account_id": self.loan_id.long_term_loan_account_id.id,
                    "credit": laon_currency_diff_amount if loan_currency_amount > 0 else 0,
                    "debit": laon_currency_diff_amount if loan_currency_amount < 0 else 0,
                    "currency_id": self.loan_id.currency_id.id,
                    "amount_currency": -1 * line.long_term_pending_principal_amount if loan_currency_amount > 0 else line.long_term_pending_principal_amount
                }
            )
        return res

    @api.private
    def move_vals(self):
        return {
            "loan_id": self.loan_id.id,
            "date": self.loan_id.start_date,
            "ref": self.loan_id.name,
            "journal_id": self.journal_id.id,
            "line_ids": [Command.create(vals) for vals in self.move_line_vals()],
        }

    def run(self):
        self.ensure_one()
        if self.loan_id.line_ids:
            total_principal = sum(self.loan_id.line_ids.mapped("principal_amount"))
            if (
                float_compare(
                    self.loan_id.loan_amount, total_principal, precision_digits=2
                )
                != 0
            ):
                raise UserError(
                    self.env._(
                        "The total principal amount does not match the loan amount."
                    )
                )
        if self.loan_id.state != "draft":
            raise UserError(self.env._("Only loans in draft state can be posted"))
        self.loan_id.post()
        move = self.env["account.move"].create(self.move_vals())
        move.action_post()
