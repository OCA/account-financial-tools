# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

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
    is_leasing = fields.Boolean(
        related="loan_id.is_leasing",
    )
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
    loan_type = fields.Selection(
        related="loan_id.loan_type",
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
                    self.loan_id._loan_rate() / 100,
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
            self.payment_amount = self.currency_id.round(self._compute_amount())
        elif not self.loan_id.round_on_end:
            self.interests_amount = self.currency_id.round(self._compute_interest())
            self.payment_amount = self.currency_id.round(self._compute_amount())
        else:
            self.interests_amount = self._compute_interest()
            self.payment_amount = self._compute_amount()

    def _compute_interest(self):
        if self.loan_type == "fixed-annuity-begin":
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

    def _move_vals(self, journal=False, account=False):
        return {
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "date": self.date,
            "ref": self.name,
            "journal_id": (journal and journal.id) or self.loan_id.journal_id.id,
            "line_ids": [
                Command.create(vals) for vals in self._move_line_vals(account=account)
            ],
        }

    def _move_line_vals(self, account=False):
        vals = []
        partner = self.loan_id.partner_id.with_company(self.loan_id.company_id)
        vals.append(
            {
                "account_id": (account and account.id)
                or partner.property_account_payable_id.id,
                "partner_id": partner.id,
                "credit": self.payment_amount,
                "debit": 0,
            }
        )
        if self.interests_amount:
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

    def _invoice_vals(self):
        return {
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "move_type": "in_invoice",
            "partner_id": self.loan_id.partner_id.id,
            "invoice_date": self.date,
            "journal_id": self.loan_id.journal_id.id,
            "company_id": self.loan_id.company_id.id,
            "invoice_line_ids": [
                Command.create(vals) for vals in self._invoice_line_vals()
            ],
        }

    def _invoice_line_vals(self):
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
                    raise UserError(_("Some moves must be created first"))
                move = self.env["account.move"].create(
                    record._move_vals(journal=journal, account=account)
                )
                move.action_post()
                res.append(move.id)
        return res

    def _long_term_move_vals(self):
        return {
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "date": self.date,
            "ref": self.name,
            "journal_id": self.loan_id.journal_id.id,
            "line_ids": [
                Command.create(vals) for vals in self._get_long_term_move_line_vals()
            ],
        }

    def _generate_invoice(self):
        """
        Computes invoices of leases
        :return: list of account.move generated
        """
        res = []
        for record in self:
            if not record.move_ids:
                if record.loan_id.line_ids.filtered(
                    lambda r, record=record: r.date < record.date and not r.move_ids
                ):
                    raise UserError(_("Some invoices must be created first"))
                invoice = self.env["account.move"].create(record._invoice_vals())
                res.append(invoice.id)
                for line in invoice.invoice_line_ids:
                    line.tax_ids = line._get_computed_taxes()
                invoice.flush_recordset()
                invoice.filtered(
                    lambda m: m.currency_id.round(m.amount_total) < 0
                ).action_switch_move_type()
                if record.loan_id.post_invoice:
                    invoice.action_post()
                if (
                    record.long_term_loan_account_id
                    and record.long_term_principal_amount != 0
                ):
                    move = self.env["account.move"].create(
                        record._long_term_move_vals()
                    )
                    if record.loan_id.post_invoice:
                        move.action_post()
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
        """Shows the invoice if it is a leasing or the move if it is a loan"""
        self.ensure_one()
        if self.is_leasing:
            return self.view_account_invoices()
        return self.view_account_moves()

    def view_process_values(self):
        """Computes the annuity and returns the result"""
        self.ensure_one()
        if self.is_leasing:
            self._generate_invoice()
        else:
            self._generate_move()
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
        result["domain"] = [("loan_line_id", "=", self.id)]
        if len(self.move_ids) == 1:
            res = self.env.ref("account.view_move_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.move_ids.id
        return result

    def view_account_invoices(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        result["context"] = {
            "default_loan_line_id": self.id,
            "default_loan_id": self.loan_id.id,
        }
        result["domain"] = [
            ("loan_line_id", "=", self.id),
        ]
        if len(self.move_ids) == 1:
            res = self.env.ref("account.view_move_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.move_ids.id
        return result
