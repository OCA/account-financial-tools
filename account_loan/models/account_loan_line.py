# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)
try:
    import numpy_financial
except (OSError, ImportError) as err:
    _logger.error(err)


class AccountLoanLine(models.Model):
    _name = "account.loan.line"
    _description = "Annuity"
    _order = "sequence asc"

    name = fields.Char(compute="_compute_name")
    loan_id = fields.Many2one(
        "account.loan",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        "res.company",
        related="loan_id.company_id",
        store=True,
    )
    partner_id = fields.Many2one("res.partner", related="loan_id.partner_id")
    journal_id = fields.Many2one(
        "account.journal",
        related="loan_id.journal_id",
    )
    short_term_loan_account_id = fields.Many2one(
        "account.account",
        related="loan_id.short_term_loan_account_id",
    )
    interest_expenses_account_id = fields.Many2one(
        "account.account",
        related="loan_id.interest_expenses_account_id",
    )
    loan_method = fields.Selection(
        related="loan_id.loan_method",
    )
    loan_state = fields.Selection(
        related="loan_id.state",
        readonly=True,
        store=True,
    )
    sequence = fields.Integer(required=True, readonly=True)
    date = fields.Date(
        required=True,
        readonly=True,
        help="Date when the payment will be accounted",
    )
    long_term_loan_account_id = fields.Many2one(
        "account.account",
        related="loan_id.long_term_loan_account_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="loan_id.currency_id",
    )
    rate = fields.Float(
        required=True,
        readonly=False,
        store=True,
        digits=(8, 6),
        compute="_compute_rate",
    )
    pending_principal_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=False,
        help="Pending amount of the loan before the payment",
    )
    long_term_pending_principal_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        help="Pending amount of the loan before the payment that will not be "
        "payed in, at least, 12 months",
    )
    payment_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=False,
        store=True,
        compute="_compute_payment_amount",
        help="Total amount that will be payed (Annuity)",
    )
    interests_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=False,
        store=True,
        compute="_compute_interests_amount",
        help="Amount of the payment that will be assigned to interests",
    )
    principal_amount = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_principal_amount",
        store=True,
        help="Amount of the payment that will reduce the pending loan amount",
    )
    long_term_principal_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        help="Amount that will reduce the pending loan amount on long term",
    )
    final_pending_principal_amount = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_amounts",
        store=True,
        help="Pending amount of the loan after the payment",
    )
    move_ids = fields.One2many(
        "account.move",
        inverse_name="loan_line_id",
    )
    has_moves = fields.Boolean(compute="_compute_has_moves")

    @api.depends("interests_amount")
    def _compute_rate(self):
        for record in self:
            rate = 0
            if not float_is_zero(record.pending_principal_amount, precision_digits=2):
                rate = (record.interests_amount * 100) / record.pending_principal_amount
            record.rate = rate

    @api.depends("rate")
    def _compute_interests_amount(self):
        for record in self:
            if record.interests_amount and record.pending_principal_amount:
                record.interests_amount = (
                    record.pending_principal_amount * record.rate
                ) / 100

    @api.depends("move_ids")
    def _compute_has_moves(self):
        for record in self:
            record.has_moves = bool(record.move_ids)

    @api.depends("loan_id.name", "sequence")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.loan_id.name}-{record.sequence}"

    @api.depends("principal_amount", "interests_amount")
    def _compute_payment_amount(self):
        for rec in self:
            rec.payment_amount = rec.principal_amount + rec.interests_amount

    @api.depends("payment_amount", "interests_amount", "pending_principal_amount")
    def _compute_amounts(self):
        for rec in self:
            rec.final_pending_principal_amount = (
                rec.pending_principal_amount - rec.payment_amount + rec.interests_amount
            )

    @api.depends("pending_principal_amount")
    def _compute_principal_amount(self):
        for rec in self:
            rec.principal_amount = rec.payment_amount - rec.interests_amount

    def _compute_amount(self):
        """
        Computes the payment amount
        :return: Amount to be payed on the annuity
        """
        if self.sequence == self.loan_id.periods:
            return (
                self.pending_principal_amount
                + self.interests_amount
                - self.loan_id.residual_amount
            )
        if self.loan_method == "fixed-principal" and self.loan_id.round_on_end:
            return self.loan_id.fixed_amount + self.interests_amount
        if self.loan_method == "fixed-principal":
            return (self.pending_principal_amount - self.loan_id.residual_amount) / (
                self.loan_id.periods - self.sequence + 1
            ) + self.interests_amount
        if self.loan_method == "interest":
            return self.interests_amount
        if self.loan_method == "fixed-annuity" and self.loan_id.round_on_end:
            return self.loan_id.fixed_amount
        if self.loan_method == "fixed-annuity":
            return self.currency_id.round(
                -numpy_financial.pmt(
                    self.loan_id._loan_rate() / 100,
                    self.loan_id.periods - self.sequence + 1,
                    self.pending_principal_amount,
                    -self.loan_id.residual_amount,
                )
            )
        if self.loan_method == "fixed-annuity-begin" and self.loan_id.round_on_end:
            return self.loan_id.fixed_amount
        if self.loan_method == "fixed-annuity-begin":
            return self.currency_id.round(
                -numpy_financial.pmt(
                    self.loan_id._loan_rate() / 100,
                    self.loan_id.periods - self.sequence + 1,
                    self.pending_principal_amount,
                    -self.loan_id.residual_amount,
                    when="begin",
                )
            )

    def _check_amount(self):
        """Recompute amounts if the annuity has not been processed"""
        if self.move_ids:
            raise UserError(
                self.env._(
                    "Amount cannot be recomputed if moves or invoices exists already"
                )
            )
        if (
            self.sequence == self.loan_id.periods
            and self.loan_id.round_on_end
            and self.loan_method in ["fixed-annuity", "fixed-annuity-begin"]
        ):
            self.interests_amount = self.currency_id.round(
                self.loan_id.fixed_amount
                - self.pending_principal_amount
                + self.loan_id.residual_amount
            )
            self.payment_amount = self.currency_id.round(self._compute_amount())
        elif not self.loan_id.round_on_end:
            self.interests_amount = self.currency_id.round(self._compute_interest())
            self.payment_amount = self.currency_id.round(self._compute_amount())
        else:
            self.interests_amount = self._compute_interest()
            self.payment_amount = self._compute_amount()

    def _compute_interest(self):
        if self.loan_method == "fixed-annuity-begin":
            return -numpy_financial.ipmt(
                self.loan_id._loan_rate() / 100,
                2,
                self.loan_id.periods - self.sequence + 1,
                self.pending_principal_amount,
                -self.loan_id.residual_amount,
                when="begin",
            )
        return self.pending_principal_amount * self.loan_id._loan_rate() / 100

    def _check_move_amount(self):
        """
        Changes the amounts of the annuity once the move is posted
        :return:
        """
        self.ensure_one()
        interests_moves = self.move_ids.mapped("line_ids").filtered(
            lambda r: r.account_id == self.loan_id.interest_expenses_account_id
        )
        short_term_moves = self.move_ids.mapped("line_ids").filtered(
            lambda r: r.account_id == self.loan_id.short_term_loan_account_id
        )
        long_term_moves = self.move_ids.mapped("line_ids").filtered(
            lambda r: r.account_id == self.loan_id.long_term_loan_account_id
        )
        interests_in_company_currency = sum(interests_moves.mapped("debit")) - sum(
            interests_moves.mapped("credit")
        )
        self.interests_amount = self.loan_id.company_id.currency_id._convert(
            from_amount=interests_in_company_currency,
            to_currency=self.loan_id.currency_id,
            company=self.loan_id.company_id,
            date=self.date,
            round=True,
        )

        long_term_principal_amount_in_company_currency = sum(
            long_term_moves.mapped("debit")
        ) - sum(long_term_moves.mapped("credit"))
        self.long_term_principal_amount = self.loan_id.company_id.currency_id._convert(
            from_amount=long_term_principal_amount_in_company_currency,
            to_currency=self.loan_id.currency_id,
            company=self.loan_id.company_id,
            date=self.date,
            round=True,
        )

        payment_amount_in_company_currency = (
            sum(short_term_moves.mapped("debit"))
            - sum(short_term_moves.mapped("credit"))
            + long_term_principal_amount_in_company_currency
            + interests_in_company_currency
        )
        self.payment_amount = self.loan_id.company_id.currency_id._convert(
            from_amount=payment_amount_in_company_currency,
            to_currency=self.loan_id.currency_id,
            company=self.loan_id.company_id,
            date=self.date,
            round=True,
        )

    def _move_vals(self, journal=False, account=False):
        self.ensure_one()
        return {
            "partner_id": self.loan_id.partner_id.with_company(
                self.loan_id.company_id
            ).id,
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "date": self.date,
            "ref": self.name,
            "journal_id": (journal and journal.id) or self.loan_id.journal_id.id,
            "line_ids": [
                Command.create(vals) for vals in self._move_line_vals(account=account)
            ],
        }

    def _add_basic_values(self, vals, account):
        self.ensure_one()
        partner = self.loan_id.partner_id.commercial_partner_id.with_company(
            self.loan_id.company_id
        )
        # Amounts are evaled if > 0 for allowing negative loans to be able to be the
        # donors of the loan
        partner_account = (
            partner.property_account_payable_id
            if self.payment_amount > 0
            else partner.property_account_receivable_id
        )
        loan_currency_amount = self.loan_id.currency_id._convert(
            from_amount=self.payment_amount,
            to_currency=self.loan_id.company_id.currency_id,
            company=self.loan_id.company_id,
            date=self.date,
            round=True,
        )
        vals.append(
            {
                "account_id": (account and account.id) or partner_account.id,
                "credit": loan_currency_amount if loan_currency_amount > 0 else 0,
                "debit": -loan_currency_amount if loan_currency_amount < 0 else 0,
                "currency_id": self.loan_id.currency_id.id,
                "amount_currency": -self.payment_amount,
            }
        )
        return vals

    def _add_interests_values(self, vals):
        self.ensure_one()
        loan_currency_amount = self.loan_id.currency_id._convert(
            from_amount=self.interests_amount,
            to_currency=self.loan_id.company_id.currency_id,
            company=self.loan_id.company_id,
            date=self.date,
            round=True,
        )
        vals.append(
            {
                "account_id": self.loan_id.interest_expenses_account_id.id,
                "credit": -loan_currency_amount if loan_currency_amount < 0 else 0,
                "debit": loan_currency_amount if loan_currency_amount > 0 else 0,
                "currency_id": self.loan_id.currency_id.id,
                "amount_currency": self.interests_amount,
            }
        )
        return vals

    def _add_short_term_account_values(self, vals):
        self.ensure_one()
        loan_currency_amount = self.loan_id.currency_id._convert(
            from_amount=self.payment_amount - self.interests_amount,
            to_currency=self.loan_id.company_id.currency_id,
            company=self.loan_id.company_id,
            date=self.date,
            round=True,
        )
        vals.append(
            {
                "account_id": self.loan_id.short_term_loan_account_id.id,
                "credit": -loan_currency_amount if loan_currency_amount < 0 else 0,
                "debit": loan_currency_amount if loan_currency_amount > 0 else 0,
                "currency_id": self.loan_id.currency_id.id,
                "amount_currency": self.payment_amount - self.interests_amount,
            }
        )
        return vals

    def _add_long_term_account_values(self, vals):
        self.ensure_one()
        if self.long_term_loan_account_id and self.long_term_principal_amount:
            loan_currency_amount = self.loan_id.currency_id._convert(
                from_amount=self.long_term_principal_amount,
                to_currency=self.loan_id.company_id.currency_id,
                company=self.loan_id.company_id,
                date=self.date,
                round=True,
            )
            vals.append(
                {
                    "account_id": self.loan_id.short_term_loan_account_id.id,
                    "credit": loan_currency_amount if loan_currency_amount > 0 else 0,
                    "debit": -loan_currency_amount if loan_currency_amount < 0 else 0,
                    "currency_id": self.loan_id.currency_id.id,
                    "amount_currency": -self.long_term_principal_amount,
                }
            )
            vals.append(
                {
                    "account_id": self.long_term_loan_account_id.id,
                    "credit": -loan_currency_amount if loan_currency_amount < 0 else 0,
                    "debit": loan_currency_amount if loan_currency_amount > 0 else 0,
                    "currency_id": self.loan_id.currency_id.id,
                    "amount_currency": self.long_term_principal_amount,
                }
            )
        return vals

    def _move_line_vals(self, account=False):
        self.ensure_one()
        vals = []
        vals = self._add_basic_values(vals, account)
        if self.interests_amount:
            vals = self._add_interests_values(vals)

        vals = self._add_short_term_account_values(vals)
        vals = self._add_long_term_account_values(vals)

        return vals

    def _generate_move(self, journal=False, account=False):
        """
        Computes and post the moves of loans
        :return: list of account.move generated
        """
        res = []
        for record in self:
            if not record.move_ids:
                if record.loan_id.line_ids.filtered(
                    lambda r, record=record: r.date < record.date and not r.move_ids
                ):
                    raise UserError(self.env._("Some moves must be created first"))
                move = self.env["account.move"].create(
                    record._move_vals(journal=journal, account=account)
                )
                move._post(soft=record.loan_id._soft_post_moves())
                res.append(move.id)
        return res

    def _get_long_term_move_line_vals(self):
        return [
            {
                "account_id": self.loan_id.short_term_loan_account_id.id,
                "credit": self.long_term_principal_amount,
                "debit": 0,
            },
            {
                "account_id": self.long_term_loan_account_id.id,
                "credit": 0,
                "debit": self.long_term_principal_amount,
            },
        ]

    def view_account_values(self):
        """Shows move if it is a loan"""
        return self.view_account_moves()

    def _generate_account_entry(self):
        self.ensure_one()
        self._generate_move()

    def view_process_values(self):
        """Computes the annuity and returns the result"""
        self.ensure_one()
        self._generate_account_entry()
        return self.view_account_values()

    def view_account_moves(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_line_form"
        )
        result["context"] = {
            "default_loan_line_id": self.id,
            "default_loan_id": self.loan_id.id,
        }
        result["domain"] = Domain("loan_line_id", "=", self.id)
        if len(self.move_ids) == 1:
            res = self.env.ref("account.view_move_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.move_ids.id
        return result
