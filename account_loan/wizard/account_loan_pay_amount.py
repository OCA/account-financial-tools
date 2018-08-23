# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class AccountLoan(models.TransientModel):
    _name = 'account.loan.pay.amount'

    loan_id = fields.Many2one(
        'account.loan',
        required=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
        readonly=True
    )
    cancel_loan = fields.Boolean(
        default=False,
    )
    date = fields.Date(required=True, default=fields.Date.today())
    amount = fields.Monetary(
        currency_field='currency_id',
        string='Amount to reduce from Principal',
    )
    fees = fields.Monetary(
        currency_field='currency_id',
        string='Bank fees'
    )

    @api.onchange('cancel_loan')
    def _onchange_cancel_loan(self):
        if self.cancel_loan:
            self.amount = max(self.loan_id.line_ids.filtered(
                lambda r: not r.move_ids and not r.invoice_ids).mapped(
                'pending_principal_amount'
            )
            )

    def new_line_val(self, sequence, date, amount):
        return {
            'loan_id': self.loan_id.id,
            'sequence': sequence,
            'date': date,
            'pending_principal_amount': amount,
            'rate': self.loan_id.rate_period,
        }

    def new_line_vals(self, sequence, date, amount, payment):
        if not self.loan_id.round_on_end:
            interests_amount = self.currency_id.round(
                amount * self.loan_id.rate_period / 100)
            if sequence == self.loan_id.periods:
                payment_amount = amount + interests_amount - self.loan_id.residual_amount
            else:
                payment_amount = self.currency_id.round(payment)
        else:

            interests_amount = (
                amount * self.loan_id.rate_period / 100)
            if sequence == self.loan_id.periods:
                payment_amount = amount + interests_amount - self.loan_id.residual_amount
            else:
                payment_amount = payment
        return {
            'loan_id': self.loan_id.id,
            'sequence': sequence,
            'payment_amount': payment_amount,
            'rate': self.loan_id.rate_period,
            'interests_amount': interests_amount,
            'date': date,
            'pending_principal_amount': amount
        }

    @api.multi
    def run(self):
        self.ensure_one()
        if self.loan_id.is_leasing:
            if self.loan_id.line_ids.filtered(
                    lambda r: r.date < self.date and not r.invoice_ids
            ):
                raise UserError(_('Some invoices are not created'))
            if self.loan_id.line_ids.filtered(
                    lambda r: r.date > self.date and r.invoice_ids
            ):
                raise UserError(_('Some future invoices already exists'))
        if self.loan_id.line_ids.filtered(
                lambda r: r.date < self.date and not r.move_ids
        ):
            raise UserError(_('Some moves are not created'))
        if self.loan_id.line_ids.filtered(
                lambda r: r.date > self.date and r.move_ids
        ):
            raise UserError(_('Some future moves already exists'))
        instalment_lines_without_move = self.loan_id.line_ids.filtered(
            lambda r: not r.move_ids).sorted('sequence')
        instalment_lines_with_move = self.loan_id.line_ids.filtered(
            lambda r: r.move_ids).sorted('sequence')
        if len(instalment_lines_without_move) == len(self.loan_id.line_ids):
            if self.loan_id.start_date:
                date = datetime.strptime(self.loan_id.start_date, DF).date()
            else:
                date = datetime.today().date()
            delta = relativedelta(months=self.loan_id.method_period)
            if not self.loan_id.payment_on_first_period:
                date += delta
            flag = False
            amount = self.loan_id.loan_amount
            if self.loan_id.is_down_payment:
                amount -= self.loan_id.down_payment
            self.loan_id.line_ids.unlink()
            for i in range(1, self.loan_id.periods + 1):
                if not flag:
                    payment = self.amount + self.fees
                    if i == self.loan_id.periods:
                        if payment > amount:
                            raise UserError(_('This is last Payment no need of extra payment'))
                    else:
                        line = self.env['account.loan.line'].create(
                            self.new_line_vals(i, date, amount, payment)
                        )
                    flag = True
                else:
                    line = self.env['account.loan.line'].create(
                        self.new_line_val(i, date, amount)
                    )
                    line.check_amount()
                date += delta
                amount -= line.payment_amount - line.interests_amount
            if self.loan_id.long_term_loan_account_id:
                self.loan_id.check_long_term_principal_amount()
            line = self.loan_id.line_ids.filtered(lambda r: r.sequence == 1)
            line.view_process_values()

        if instalment_lines_with_move:
            instalment_lines_without_move.unlink()
            sequence = max(instalment_lines_with_move.mapped('sequence')) + 1
            old_line = instalment_lines_with_move.filtered(lambda r: r.sequence == sequence - 1)
            amount = old_line.final_pending_principal_amount
            date = datetime.strptime(old_line.date, DF).date()
            delta = relativedelta(months=self.loan_id.method_period)
            date += delta
            flag = False
            for i in range(sequence, self.loan_id.periods + 1):
                if not flag:
                    payment = self.amount + self.fees
                    line = self.env['account.loan.line'].create(
                        self.new_line_vals(i, date, amount, payment)
                    )
                    flag = True
                    if i == self.loan_id.periods:
                        if payment > amount:
                            raise UserError(_('This is last Payment no need of extra payment'))
                else:
                    line = self.env['account.loan.line'].create(
                        self.new_line_val(i, date, amount)
                    )
                    line.check_amount()
                date += delta
                amount -= line.payment_amount - line.interests_amount
            if self.loan_id.long_term_loan_account_id:
                self.loan_id.check_long_term_principal_amount()
            line = self.loan_id.line_ids.filtered(lambda r: r.sequence == sequence)
            line.view_process_values()
