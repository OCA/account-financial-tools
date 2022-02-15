# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    import numpy_financial
except (ImportError, IOError) as err:
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
    is_leasing = fields.Boolean(
        related="loan_id.is_leasing",
        readonly=True,
    )
    loan_type = fields.Selection(
        related="loan_id.loan_type",
        readonly=True,
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
        readonly=True,
        related="loan_id.long_term_loan_account_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="loan_id.currency_id",
    )
    rate = fields.Float(
        required=True,
        readonly=True,
        digits=(8, 6),
    )
    pending_principal_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
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
        readonly=True,
        help="Total amount that will be payed (Annuity)",
    )
    interests_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        help="Amount of the payment that will be assigned to interests",
    )
    principal_amount = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_amounts",
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
        help="Pending amount of the loan after the payment",
    )
    move_ids = fields.One2many(
        "account.move",
        inverse_name="loan_line_id",
    )
    has_moves = fields.Boolean(compute="_compute_has_moves")
    has_invoices = fields.Boolean(compute="_compute_has_invoices")
    _sql_constraints = [
        (
            "sequence_loan",
            "unique(loan_id, sequence)",
            "Sequence must be unique in a loan",
        )
    ]

    @api.depends("move_ids")
    def _compute_has_moves(self):
        for record in self:
            record.has_moves = bool(record.move_ids)

    @api.depends("move_ids")
    def _compute_has_invoices(self):
        for record in self:
            record.has_invoices = bool(record.move_ids)

    @api.depends("loan_id.name", "sequence")
    def _compute_name(self):
        for record in self:
            record.name = "%s-%d" % (record.loan_id.name, record.sequence)

    @api.depends("payment_amount", "interests_amount", "pending_principal_amount")
    def _compute_amounts(self):
        for rec in self:
            rec.final_pending_principal_amount = (
                rec.pending_principal_amount - rec.payment_amount + rec.interests_amount
            )
            rec.principal_amount = rec.payment_amount - rec.interests_amount

    def compute_amount(self):
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
        if self.loan_type == "fixed-principal" and self.loan_id.round_on_end:
            return self.loan_id.fixed_amount + self.interests_amount
        if self.loan_type == "fixed-principal":
            return (self.pending_principal_amount - self.loan_id.residual_amount) / (
                self.loan_id.periods - self.sequence + 1
            ) + self.interests_amount
        if self.loan_type == "interest":
            return self.interests_amount
        if self.loan_type == "fixed-annuity" and self.loan_id.round_on_end:
            return self.loan_id.fixed_amount
        if self.loan_type == "fixed-annuity":
            return self.currency_id.round(
                -numpy_financial.pmt(
                    self.loan_id.loan_rate() / 100,
                    self.loan_id.periods - self.sequence + 1,
                    self.pending_principal_amount,
                    -self.loan_id.residual_amount,
                )
            )
        if self.loan_type == "fixed-annuity-begin" and self.loan_id.round_on_end:
            return self.loan_id.fixed_amount
        if self.loan_type == "fixed-annuity-begin":
            return self.currency_id.round(
                -numpy_financial.pmt(
                    self.loan_id.loan_rate() / 100,
                    self.loan_id.periods - self.sequence + 1,
                    self.pending_principal_amount,
                    -self.loan_id.residual_amount,
                    when="begin",
                )
            )

    def check_amount(self):
        """Recompute amounts if the annuity has not been processed"""
        if self.move_ids:
            raise UserError(
                _("Amount cannot be recomputed if moves or invoices exists " "already")
            )
        if (
            self.sequence == self.loan_id.periods
            and self.loan_id.round_on_end
            and self.loan_type in ["fixed-annuity", "fixed-annuity-begin"]
        ):
            self.interests_amount = self.currency_id.round(
                self.loan_id.fixed_amount
                - self.pending_principal_amount
                + self.loan_id.residual_amount
            )
            self.payment_amount = self.currency_id.round(self.compute_amount())
        elif not self.loan_id.round_on_end:
            self.interests_amount = self.currency_id.round(self.compute_interest())
            self.payment_amount = self.currency_id.round(self.compute_amount())
        else:
            self.interests_amount = self.compute_interest()
            self.payment_amount = self.compute_amount()

    def compute_interest(self):
        if self.loan_type == "fixed-annuity-begin":
            return -numpy_financial.ipmt(
                self.loan_id.loan_rate() / 100,
                2,
                self.loan_id.periods - self.sequence + 1,
                self.pending_principal_amount,
                -self.loan_id.residual_amount,
                when="begin",
            )
        return self.pending_principal_amount * self.loan_id.loan_rate() / 100

    def check_move_amount(self):
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
        self.interests_amount = sum(interests_moves.mapped("debit")) - sum(
            interests_moves.mapped("credit")
        )
        self.long_term_principal_amount = sum(long_term_moves.mapped("debit")) - sum(
            long_term_moves.mapped("credit")
        )
        self.payment_amount = (
            sum(short_term_moves.mapped("debit"))
            - sum(short_term_moves.mapped("credit"))
            + self.long_term_principal_amount
            + self.interests_amount
        )

    def move_vals(self):
        return {
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "date": self.date,
            "ref": self.name,
            "journal_id": self.loan_id.journal_id.id,
            "line_ids": [(0, 0, vals) for vals in self.move_line_vals()],
        }

    def move_line_vals(self):
        vals = []
        partner = self.loan_id.partner_id.with_company(self.loan_id.company_id)
        vals.append(
            {
                "account_id": partner.property_account_payable_id.id,
                "partner_id": partner.id,
                "credit": self.payment_amount,
                "debit": 0,
            }
        )
        vals.append(
            {
                "account_id": self.loan_id.interest_expenses_account_id.id,
                "credit": 0,
                "debit": self.interests_amount,
            }
        )
        vals.append(
            {
                "account_id": self.loan_id.short_term_loan_account_id.id,
                "credit": 0,
                "debit": self.payment_amount - self.interests_amount,
            }
        )
        if self.long_term_loan_account_id and self.long_term_principal_amount:
            vals.append(
                {
                    "account_id": self.loan_id.short_term_loan_account_id.id,
                    "credit": self.long_term_principal_amount,
                    "debit": 0,
                }
            )
            vals.append(
                {
                    "account_id": self.long_term_loan_account_id.id,
                    "credit": 0,
                    "debit": self.long_term_principal_amount,
                }
            )
        return vals

    def invoice_vals(self):
        return {
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "move_type": "in_invoice",
            "partner_id": self.loan_id.partner_id.id,
            "invoice_date": self.date,
            "journal_id": self.loan_id.journal_id.id,
            "company_id": self.loan_id.company_id.id,
            "invoice_line_ids": [(0, 0, vals) for vals in self.invoice_line_vals()],
        }

    def invoice_line_vals(self):
        vals = list()
        vals.append(
            {
                "product_id": self.loan_id.product_id.id,
                "name": self.loan_id.product_id.name,
                "quantity": 1,
                "price_unit": self.principal_amount,
                "account_id": self.loan_id.short_term_loan_account_id.id,
            }
        )
        vals.append(
            {
                "product_id": self.loan_id.interests_product_id.id,
                "name": self.loan_id.interests_product_id.name,
                "quantity": 1,
                "price_unit": self.interests_amount,
                "account_id": self.loan_id.interest_expenses_account_id.id,
            }
        )
        return vals

    def generate_move(self):
        """
        Computes and post the moves of loans
        :return: list of account.move generated
        """
        res = []
        for record in self:
            if not record.move_ids:
                if record.loan_id.line_ids.filtered(
                    lambda r: r.date < record.date and not r.move_ids
                ):
                    raise UserError(_("Some moves must be created first"))
                move = self.env["account.move"].create(record.move_vals())
                move.action_post()
                res.append(move.id)
        return res

    def generate_invoice(self):
        """
        Computes invoices of leases
        :return: list of account.move generated
        """
        res = []
        for record in self:
            if not record.move_ids:
                if record.loan_id.line_ids.filtered(
                    lambda r: r.date < record.date and not r.move_ids
                ):
                    raise UserError(_("Some invoices must be created first"))
                invoice = self.env["account.move"].create(record.invoice_vals())
                res.append(invoice.id)
                for line in invoice.invoice_line_ids:
                    line.tax_ids = line._get_computed_taxes()
                invoice.with_context(
                    check_move_validity=False
                )._recompute_dynamic_lines(recompute_all_taxes=True)
                invoice._check_balanced()
                if (
                    record.long_term_loan_account_id
                    and record.long_term_principal_amount != 0
                ):
                    invoice.write({"line_ids": record._get_long_term_move_line_vals()})
                if record.loan_id.post_invoice:
                    invoice.action_post()
        return res

    def _get_long_term_move_line_vals(self):
        return [
            (
                0,
                0,
                {
                    "account_id": self.loan_id.short_term_loan_account_id.id,
                    "credit": self.long_term_principal_amount,
                    "debit": 0,
                    "exclude_from_invoice_tab": True,
                },
            ),
            (
                0,
                0,
                {
                    "account_id": self.long_term_loan_account_id.id,
                    "credit": 0,
                    "debit": self.long_term_principal_amount,
                    "exclude_from_invoice_tab": True,
                },
            ),
        ]

    def view_account_values(self):
        """Shows the invoice if it is a leasing or the move if it is a loan"""
        self.ensure_one()
        if self.is_leasing:
            return self.view_account_invoices()
        return self.view_account_moves()

    def view_process_values(self):
        """Computes the annuity and returns the result"""
        self.ensure_one()
        if self.is_leasing:
            self.generate_invoice()
        else:
            self.generate_move()
        return self.view_account_values()

    def view_account_moves(self):
        self.ensure_one()
        action = self.env.ref("account.action_move_line_form")
        result = action.read()[0]
        result["context"] = {
            "default_loan_line_id": self.id,
            "default_loan_id": self.loan_id.id,
        }
        result["domain"] = [("loan_line_id", "=", self.id)]
        if len(self.move_ids) == 1:
            res = self.env.ref("account.move.form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.move_ids.id
        return result

    def view_account_invoices(self):
        self.ensure_one()
        action = self.env.ref("account.action_move_out_invoice_type")
        result = action.read()[0]
        result["context"] = {
            "default_loan_line_id": self.id,
            "default_loan_id": self.loan_id.id,
        }
        result["domain"] = [
            ("loan_line_id", "=", self.id),
            ("move_type", "=", "in_invoice"),
        ]
        if len(self.move_ids) == 1:
            res = self.env.ref("account.view_move_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.move_ids.id
        return result
