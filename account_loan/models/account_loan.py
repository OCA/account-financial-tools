# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import math
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain
from odoo.tools.misc import str2bool

_logger = logging.getLogger(__name__)
try:
    import numpy_financial
except (OSError, ImportError) as err:
    _logger.debug(err)


class AccountLoan(models.Model):
    _name = "account.loan"
    _description = "Loan"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_company(self):
        return self.env.company

    name = fields.Char(
        copy=False,
        required=True,
        default="/",
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        string="Lender",
        help="Company or individual that lends the money at an interest rate.",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self._default_company(),
    )
    loan_type = fields.Selection(
        [
            ("loan", "loan"),
            ("borrow", "Borrow"),
        ],
        default="loan",
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
            ("closed", "Closed"),
        ],
        required=True,
        copy=False,
        default="draft",
    )
    line_ids = fields.One2many(
        "account.loan.line",
        readonly=True,
        inverse_name="loan_id",
        copy=False,
    )
    periods = fields.Integer(
        required=True,
        help="Number of periods that the loan will last",
    )
    method_period = fields.Integer(
        string="Period Length",
        default=1,
        help="State here the time between 2 depreciations, in months",
        required=True,
    )
    start_date = fields.Date(
        help="Start of the moves",
        copy=False,
    )
    rate = fields.Float(
        required=True,
        default=0.0,
        digits=(8, 6),
        help="Currently applied rate",
        tracking=True,
    )
    rate_period = fields.Float(
        compute="_compute_rate_period",
        digits=(8, 6),
        help="Real rate that will be applied on each period",
    )
    rate_type = fields.Selection(
        [("napr", "Nominal APR"), ("ear", "EAR"), ("real", "Real rate")],
        required=True,
        help="Method of computation of the applied rate",
        default="napr",
    )
    loan_method = fields.Selection(
        [
            ("fixed-annuity", "Fixed Annuity"),
            ("fixed-annuity-begin", "Fixed Annuity Begin"),
            ("fixed-principal", "Fixed Principal"),
            ("interest", "Only interest"),
        ],
        required=True,
        help="Method of computation of the period annuity",
        default="fixed-annuity",
    )
    fixed_amount = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_fixed_amount",
    )
    fixed_loan_amount = fields.Monetary(
        currency_field="currency_id",
        readonly=True,
        copy=False,
        default=0,
    )
    fixed_periods = fields.Integer(
        readonly=True,
        copy=False,
        default=0,
    )
    loan_amount = fields.Monetary(
        currency_field="currency_id",
        required=True,
    )
    residual_amount = fields.Monetary(
        currency_field="currency_id",
        default=0.0,
        required=True,
        help="Residual amount of the lease that must be payed on the end in "
        "order to acquire the asset",
    )
    round_on_end = fields.Boolean(
        help="When checked, the differences will be applied on the last period"
        ", if it is unchecked, the annuity will be recalculated on each "
        "period.",
    )
    payment_on_first_period = fields.Boolean(
        help="When checked, the first payment will be on start date",
    )
    currency_id = fields.Many2one(
        "res.currency", compute="_compute_currency", readonly=False, store=True
    )
    journal_id = fields.Many2one(
        "account.journal",
        domain="[('company_id', '=', company_id)]",
        compute="_compute_journal_id",
        readonly=False,
        store=True,
        required=True,
        check_company=True,
    )
    short_term_loan_account_id = fields.Many2one(
        "account.account",
        domain="[('company_ids', '=', company_id)]",
        string="Short term account",
        help="Account that will contain the pending amount on short term",
        required=True,
    )
    long_term_loan_account_id = fields.Many2one(
        "account.account",
        string="Long term account",
        help="Account that will contain the pending amount on Long term",
        domain="[('company_ids', '=', company_id)]",
    )
    interest_expenses_account_id = fields.Many2one(
        "account.account",
        domain="[('company_ids', '=', company_id)]",
        string="Interests account",
        help="Account where the interests will be assigned to",
        required=True,
    )
    move_ids = fields.One2many("account.move", copy=False, inverse_name="loan_id")
    move_count = fields.Integer(compute="_compute_move_count")
    pending_principal_amount = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_total_amounts",
    )
    payment_amount = fields.Monetary(
        currency_field="currency_id",
        string="Total payed amount",
        compute="_compute_total_amounts",
    )
    interests_amount = fields.Monetary(
        currency_field="currency_id",
        string="Total interests payed",
        compute="_compute_total_amounts",
    )

    _unique_name = models.Constraint(
        "unique(name, company_id)",
        message="Loan name must be unique",
    )

    def _check_laon_type_constrains(self):
        self.ensure_one()
        if self.loan_type == "loan" and self.loan_amount < 0:
            raise ValidationError(
                self.env._("Loan type must have postive amount or change the type")
            )
        if self.loan_type == "borrow" and self.loan_amount > 0:
            raise ValidationError(
                self.env._("Borrow type must have negative amount or change the type")
            )

    @api.model
    def _soft_post_moves(self):
        """
        Inhertiance hook to conditon posting move
        at move date or right now

        (It's used like this move._post(soft=loan_id._soft_post_moves())
        """
        return str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("account_loan.auto_post_loan_moves_at_date", "false")
        )

    @api.constrains("loan_amount", "loan_type")
    def _check_loan_type_constrains(self):
        for loan in self:
            loan._check_laon_type_constrains()

    @api.constrains("journal_id", "company_id", "loan_type")
    def _check_journal_type_allowed(self):
        for loan in self:
            if (
                self.env["account.journal"].search_count(
                    Domain("id", "=", loan.journal_id.id) & loan._journal_domain()
                )
                == 0
            ):
                raise ValidationError(
                    self.env._(
                        "The current journal %(journal_name)s type: %(journal_type)s "
                        "(company %(journal_company_name)s) is not allowed for this "
                        "type %(loan_type)s",
                        journal_name=loan.journal_id.name,
                        journal_type=loan.journal_id.type,
                        journal_company_name=loan.journal_id.company_id.name,
                        loan_type=loan.loan_type,
                    )
                )

    @api.onchange("rate")
    def _onchange_rate_warning(self):
        if self.state != "draft":
            return {
                "warning": {
                    "title": self.env._("Rate Change"),
                    "message": self.env._(
                        "You have modified the interest rate. Click the Compute items "
                        "button to update the lines. Please note that if you have "
                        "manually edited these lines, those changes will be lost upon "
                        "computation."
                    ),
                }
            }

    @api.onchange("line_ids")
    def _onchange_line_ids_draft_manual(self):
        self.line_ids = self.line_ids.sorted(key=lambda line: line.sequence)
        previous_pending_principal = 0
        previous_principal_amount = 0
        for line in self.line_ids:
            if line.sequence == 1:
                line.pending_principal_amount = line.loan_id.loan_amount
            else:
                line.pending_principal_amount = (
                    previous_pending_principal - previous_principal_amount
                )
            previous_pending_principal = line.pending_principal_amount
            previous_principal_amount = line.principal_amount

    @api.depends("loan_type", "company_id")
    def _compute_journal_id(self):
        for loan in self:
            loan.journal_id = self.env["account.journal"].search(
                self._journal_domain(), limit=1
            )

    def _journal_domain(self):
        self.ensure_one()
        return (
            Domain("company_id", "=", self.company_id.id or self.env.company.id)
            & self._journal_type_domain()
        )

    def _journal_type_domain(self):
        if self.loan_type in ("loan", "borrow"):
            return Domain("type", "=", "general")
        return Domain([])

    @api.depends("move_ids")
    def _compute_move_count(self):
        for item in self:
            item.move_count = len(item.move_ids)

    @api.depends("line_ids", "currency_id", "loan_amount")
    def _compute_total_amounts(self):
        for record in self:
            lines = record.line_ids.filtered(lambda r: r.move_ids)
            record.payment_amount = sum(lines.mapped("payment_amount")) or 0.0
            record.interests_amount = sum(lines.mapped("interests_amount")) or 0.0
            record.pending_principal_amount = (
                record.loan_amount - record.payment_amount + record.interests_amount
            )

    @api.depends("rate_period", "fixed_loan_amount", "fixed_periods", "currency_id")
    def _compute_fixed_amount(self):
        """
        Computes the fixed amount in order to be used if round_on_end is
        checked. On fix-annuity interests are included and on fixed-principal
        and interests it isn't.
        :return:
        """
        for record in self:
            if record.loan_method == "fixed-annuity":
                record.fixed_amount = -record.currency_id.round(
                    numpy_financial.pmt(
                        record._loan_rate() / 100,
                        record.fixed_periods,
                        record.fixed_loan_amount,
                        -record.residual_amount,
                    )
                )
            elif record.loan_method == "fixed-annuity-begin":
                record.fixed_amount = -record.currency_id.round(
                    numpy_financial.pmt(
                        record._loan_rate() / 100,
                        record.fixed_periods,
                        record.fixed_loan_amount,
                        -record.residual_amount,
                        when="begin",
                    )
                )
            elif record.loan_method == "fixed-principal":
                record.fixed_amount = record.currency_id.round(
                    (record.fixed_loan_amount - record.residual_amount)
                    / record.fixed_periods
                )
            else:
                record.fixed_amount = 0.0

    @api.model
    def _compute_rate(self, rate, rate_type, method_period):
        """
        Returns the real rate
        :param rate: Rate
        :param rate_type: Computation rate
        :param method_period: Number of months between payments
        :return:
        """
        if rate_type == "napr":
            return rate / 12 * method_period
        if rate_type == "ear":
            return math.pow(1 + rate, method_period / 12) - 1
        return rate

    @api.depends("rate", "method_period", "rate_type")
    def _compute_rate_period(self):
        for record in self:
            record.rate_period = record._loan_rate()

    def _loan_rate(self):
        return self._compute_rate(self.rate, self.rate_type, self.method_period)

    @api.depends("journal_id", "company_id")
    def _compute_currency(self):
        for rec in self:
            rec.currency_id = rec.journal_id.currency_id or rec.company_id.currency_id

    @api.onchange("company_id")
    def _onchange_company(self):
        self.interest_expenses_account_id = self.short_term_loan_account_id = (
            self.long_term_loan_account_id
        ) = False

    def _get_default_name(self, vals):
        return self.env["ir.sequence"].next_by_code("account.loan") or "/"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self._get_default_name(vals)
        return super().create(vals_list)

    @api.private
    def post(self):
        self.ensure_one()
        if not self.start_date:
            self.start_date = fields.Date.today()
        if not self.line_ids:
            self._compute_draft_lines()
        self.write({"state": "posted"})

    def close(self):
        self.write({"state": "closed"})

    def compute_lines(self):
        self.ensure_one()
        if self.state == "draft":
            return self._compute_draft_lines()
        return self._compute_posted_lines()

    def _compute_posted_lines(self):
        """
        Recompute the amounts of not finished lines. Useful if rate is changed
        """
        amount = self.loan_amount
        for line in self.line_ids.sorted("sequence"):
            if line.move_ids:
                amount = line.final_pending_principal_amount
            else:
                line.rate = self.rate_period
                line.pending_principal_amount = amount
                line._check_amount()
                amount -= line.payment_amount - line.interests_amount
        if self.long_term_loan_account_id:
            self._check_long_term_principal_amount()

    def _check_long_term_principal_amount(self):
        """
        Recomputes the long term pending principal of unfinished lines.
        """
        lines = self.line_ids.filtered(lambda r: not r.move_ids)
        amount = 0
        if not lines:
            return
        final_sequence = min(lines.mapped("sequence"))
        for line in lines.sorted("sequence", reverse=True):
            date = line.date + relativedelta(months=12)
            if self.state == "draft" or line.sequence != final_sequence:
                line.long_term_pending_principal_amount = sum(
                    self.line_ids.filtered(lambda r, date=date: r.date >= date).mapped(
                        "principal_amount"
                    )
                )
            line.long_term_principal_amount = (
                line.long_term_pending_principal_amount - amount
            )
            amount = line.long_term_pending_principal_amount

    def _new_line_vals(self, sequence, date, amount):
        return {
            "loan_id": self.id,
            "sequence": sequence,
            "date": date,
            "pending_principal_amount": amount,
            "rate": self.rate_period,
        }

    def _compute_draft_lines(self):
        self.ensure_one()
        self.fixed_periods = self.periods
        self.fixed_loan_amount = self.loan_amount
        self.line_ids.unlink()
        amount = self.loan_amount
        if self.start_date:
            date = self.start_date
        else:
            date = datetime.today().date()
        initial_date = date
        delta = relativedelta(months=self.method_period)
        if not self.payment_on_first_period:
            date = initial_date + delta
            initial_date = date
        for i in range(1, self.periods + 1):
            line = self.env["account.loan.line"].create(
                self._new_line_vals(i, date, amount)
            )
            line._check_amount()
            date = initial_date + delta * i
            amount -= line.payment_amount - line.interests_amount
        if self.long_term_loan_account_id:
            self._check_long_term_principal_amount()

    def button_draft(self):
        for item in self:
            if item.state not in ("posted", "cancelled") or item.move_count > 0:
                raise UserError(
                    self.env._(
                        "It is only possible to change to draft if the status is "
                        "cancelled or posted and there are no account moves."
                    )
                )
            item.state = "draft"

    def view_account_moves(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_line_form"
        )
        result["domain"] = Domain("loan_id", "=", self.id)
        return result

    @api.model
    def _loan_and_borrow_domain(self):
        return Domain([])

    @api.model
    def _generate_loan_entries(self, date):
        """
        Generate the moves of unfinished loans before date
        :param date:
        :return:
        """
        res = []
        for record in self.search(
            Domain("state", "=", "posted") & self._loan_and_borrow_domain()
        ):
            lines = record.line_ids.filtered(
                lambda r: r.date <= date and not r.move_ids
            )
            res += lines._generate_move()
        return res
