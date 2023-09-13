# Copyright 2018-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar
import time
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class AccountSpread(models.Model):
    _name = "account.spread"
    _description = "Account Spread"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True)
    template_id = fields.Many2one("account.spread.template", string="Spread Template")
    invoice_type = fields.Selection(
        [
            ("out_invoice", "Customer Invoice"),
            ("in_invoice", "Vendor Bill"),
            ("out_refund", "Customer Credit Note"),
            ("in_refund", "Vendor Credit Note"),
        ],
        required=True,
    )
    spread_type = fields.Selection(
        [("sale", "Customer"), ("purchase", "Supplier")],
        compute="_compute_spread_type",
        required=True,
    )
    period_number = fields.Integer(
        string="Number of Repetitions",
        default=12,
        help="Define the number of spread lines",
        required=True,
    )
    period_type = fields.Selection(
        [("month", "Month"), ("quarter", "Quarter"), ("year", "Year")],
        default="month",
        help="Period length for the entries",
        required=True,
    )
    days_calc = fields.Boolean(
        string="Calculate by days",
        default=False,
        help="Use number of days to calculate amount",
    )
    use_invoice_line_account = fields.Boolean()
    credit_account_id = fields.Many2one(
        "account.account",
        compute="_compute_credit_account_id",
        readonly=False,
        store=True,
        required=True,
    )
    debit_account_id = fields.Many2one(
        "account.account",
        compute="_compute_debit_account_id",
        readonly=False,
        store=True,
        required=True,
    )
    is_credit_account_deprecated = fields.Boolean(
        compute="_compute_deprecated_accounts"
    )
    is_debit_account_deprecated = fields.Boolean(compute="_compute_deprecated_accounts")
    unspread_amount = fields.Float(
        digits="Account",
        compute="_compute_amounts",
    )
    unposted_amount = fields.Float(
        digits="Account",
        compute="_compute_amounts",
    )
    posted_amount = fields.Float(
        digits="Account",
        compute="_compute_amounts",
    )
    total_amount = fields.Float(
        digits="Account",
        compute="_compute_amounts",
    )
    all_posted = fields.Boolean(compute="_compute_all_posted", store=True)
    line_ids = fields.One2many(
        "account.spread.line", "spread_id", string="Spread Lines"
    )
    spread_date = fields.Date(
        string="Start Date", default=time.strftime("%Y-01-01"), required=True
    )
    journal_id = fields.Many2one(
        "account.journal",
        compute="_compute_journal_id",
        readonly=False,
        store=True,
        required=True,
    )
    invoice_line_ids = fields.One2many(
        "account.move.line", "spread_id", copy=False, string="Invoice Lines"
    )
    invoice_line_id = fields.Many2one(
        "account.move.line",
        string="Invoice line",
        compute="_compute_invoice_line",
        inverse="_inverse_invoice_line",
        store=True,
    )
    invoice_id = fields.Many2one(
        related="invoice_line_id.move_id",
        readonly=True,
        store=True,
    )
    estimated_amount = fields.Float(digits="Account")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    account_analytic_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account"
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    move_line_auto_post = fields.Boolean("Auto-post lines", default=True)
    display_create_all_moves = fields.Boolean(
        compute="_compute_display_create_all_moves",
    )
    display_recompute_buttons = fields.Boolean(
        compute="_compute_display_recompute_buttons",
    )
    display_move_line_auto_post = fields.Boolean(
        compute="_compute_display_move_line_auto_post",
        string="Display Button Auto-post lines",
    )
    active = fields.Boolean(default=True)

    @api.model
    def default_journal(self, company_id):
        domain = [("type", "=", "general"), ("company_id", "=", company_id)]
        return self.env["account.journal"].search(domain, limit=1)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "journal_id" not in res:
            company_id = res.get("company_id", self.env.company.id)
            default_journal = self.default_journal(company_id)
            if default_journal:
                res["journal_id"] = default_journal.id
        return res

    @api.depends("invoice_type")
    def _compute_spread_type(self):
        for spread in self:
            if spread.invoice_type in ["out_invoice", "out_refund"]:
                spread.spread_type = "sale"
            else:
                spread.spread_type = "purchase"

    @api.depends("invoice_line_ids", "invoice_line_ids.move_id")
    def _compute_invoice_line(self):
        for spread in self:
            invoice_lines = spread.invoice_line_ids
            spread.invoice_line_id = invoice_lines and invoice_lines[0] or False

    def _inverse_invoice_line(self):
        for spread in self:
            invoice_line = spread.invoice_line_id
            spread.write({"invoice_line_ids": [(6, 0, [invoice_line.id])]})

    @api.depends(
        "estimated_amount",
        "currency_id",
        "company_id",
        "invoice_line_id.price_subtotal",
        "invoice_line_id.currency_id",
        "line_ids.amount",
        "line_ids.move_id.state",
    )
    def _compute_amounts(self):
        for spread in self:
            lines_move = spread.line_ids.filtered(lambda l: l.move_id)
            moves_amount = sum(spread_line.amount for spread_line in lines_move)
            lines_posted = lines_move.filtered(lambda l: l.move_id.state == "posted")
            posted_amount = sum(spread_line.amount for spread_line in lines_posted)
            total_amount = spread.estimated_amount
            if spread.invoice_line_id:
                total_amount = spread.invoice_line_id.currency_id._convert(
                    spread.invoice_line_id.balance,
                    spread.currency_id,
                    spread.company_id,
                    spread.invoice_id.date,
                )

            spread.unspread_amount = total_amount - moves_amount
            spread.unposted_amount = total_amount - posted_amount
            spread.posted_amount = posted_amount
            spread.total_amount = total_amount

    @api.depends("unposted_amount")
    def _compute_all_posted(self):
        for spread in self:
            rounding = self.currency_id.rounding
            unposted = spread.unposted_amount
            spread.all_posted = float_is_zero(unposted, precision_rounding=rounding)

    def _compute_display_create_all_moves(self):
        for spread in self:
            any_not_move = any(not line.move_id for line in spread.line_ids)
            spread.display_create_all_moves = any_not_move

    def _compute_display_recompute_buttons(self):
        for spread in self:
            spread.display_recompute_buttons = True
            if not spread.company_id.allow_spread_planning:
                if spread.invoice_id.state == "draft":
                    spread.display_recompute_buttons = False

    @api.depends("company_id.force_move_auto_post")
    def _compute_display_move_line_auto_post(self):
        for spread in self:
            auto_post = spread.company_id.force_move_auto_post
            spread.display_move_line_auto_post = not auto_post

    def _get_spread_entry_name(self, seq):
        """Use this method to customise the name of the accounting entry."""
        self.ensure_one()
        return (self.name or "") + "/" + str(seq)

    @api.onchange("template_id")
    def onchange_template(self):
        if self.template_id:
            if self.template_id.spread_type == "sale":
                if self.invoice_type in ["in_invoice", "in_refund"]:
                    self.invoice_type = "out_invoice"
            else:
                if self.invoice_type in ["out_invoice", "out_refund"]:
                    self.invoice_type = "in_invoice"
            if self.template_id.period_number:
                self.period_number = self.template_id.period_number
            if self.template_id.period_type:
                self.period_type = self.template_id.period_type
            if self.template_id.start_date:
                self.spread_date = self.template_id.start_date
            self.days_calc = self.template_id.days_calc

    @api.depends("invoice_type", "company_id")
    def _compute_journal_id(self):
        if not self.env.context.get("default_journal_id"):
            for spread in self:
                journal = spread.company_id.default_spread_expense_journal_id
                if spread.invoice_type in ("out_invoice", "in_refund"):
                    journal = spread.company_id.default_spread_revenue_journal_id
                if not journal:
                    journal = self.default_journal(spread.company_id.id)
                spread.journal_id = journal

    @api.depends("invoice_type", "company_id")
    def _compute_debit_account_id(self):
        if not self.env.context.get("default_debit_account_id"):
            invoice_types = ("out_invoice", "in_refund")
            for spread in self.filtered(lambda s: s.invoice_type in invoice_types):
                debit_account = spread.company_id.default_spread_revenue_account_id
                spread.debit_account_id = debit_account

    @api.depends("invoice_type", "company_id")
    def _compute_credit_account_id(self):
        if not self.env.context.get("default_credit_account_id"):
            invoice_types = ("in_invoice", "out_refund")
            for spread in self.filtered(lambda s: s.invoice_type in invoice_types):
                credit_account = spread.company_id.default_spread_expense_account_id
                spread.credit_account_id = credit_account

    @api.constrains("invoice_id", "invoice_type")
    def _check_invoice_type(self):
        if self.filtered(
            lambda s: s.invoice_id and s.invoice_type != s.invoice_id.move_type
        ):
            raise ValidationError(
                _("The Invoice Type does not correspond to the Invoice")
            )

    @api.constrains("journal_id")
    def _check_journal(self):
        for spread in self:
            moves = spread.mapped("line_ids.move_id").filtered("journal_id")
            if any(move.journal_id != spread.journal_id for move in moves):
                err_msg = _("The Journal is not consistent with the account moves.")
                raise ValidationError(err_msg)

    @api.constrains("template_id", "invoice_type")
    def _check_template_invoice_type(self):
        for spread in self.filtered(lambda s: s.template_id.spread_type == "sale"):
            if spread.invoice_type in ["in_invoice", "in_refund"]:
                err_msg = _(
                    "The Spread Template (Sales) is not compatible "
                    "with selected invoice type"
                )
                raise ValidationError(err_msg)
        for spread in self.filtered(lambda s: s.template_id.spread_type == "purchase"):
            if spread.invoice_type in ["out_invoice", "out_refund"]:
                err_msg = _(
                    "The Spread Template (Purchases) is not compatible "
                    "with selected invoice type"
                )
                raise ValidationError(err_msg)

    def _get_spread_period_duration(self):
        """Converts the selected period_type to number of months."""
        self.ensure_one()
        if self.period_type == "year":
            return 12
        elif self.period_type == "quarter":
            return 3
        return 1

    def _init_line_date(self, posted_line_ids):
        """Calculates the initial spread date. This method
        is used by "def _compute_spread_board()" method.
        """
        self.ensure_one()
        if posted_line_ids:
            # if we already have some previous validated entries,
            # starting date is last entry + method period
            last_date = posted_line_ids[-1].date
            months = self._get_spread_period_duration()
            spread_date = last_date + relativedelta(months=months)
        else:
            spread_date = self.spread_date
        return spread_date

    def _next_line_date(self, month_day, date):
        """Calculates the next spread date. This method
        is used by "def _compute_spread_board()" method.
        """
        self.ensure_one()
        months = self._get_spread_period_duration()
        date = date + relativedelta(months=months)
        # get the last day of the month
        if month_day > 28:
            max_day_in_month = calendar.monthrange(date.year, date.month)[1]
            date = date.replace(day=min(max_day_in_month, month_day))
        return date

    def _compute_spread_board(self):
        """Creates the spread lines. This method is highly inspired
        from method compute_depreciation_board() present in standard
        Odoo 11.0 "account_asset" module, developed by Odoo SA.
        """
        self.ensure_one()

        posted_line_ids = self.line_ids.filtered(
            lambda x: x.move_id.state == "posted"
        ).sorted(key=lambda l: l.date)
        unposted_line_ids = self.line_ids.filtered(
            lambda x: not x.move_id.state == "posted"
        )

        # Remove old unposted spread lines.
        commands = [(2, line_id.id, False) for line_id in unposted_line_ids]

        if self.unposted_amount != 0.0:
            unposted_amount = self.unposted_amount

            spread_date = self._init_line_date(posted_line_ids)

            month_day = spread_date.day
            number_of_periods = self._get_number_of_periods(month_day)

            for x in range(len(posted_line_ids), number_of_periods):
                sequence = x + 1
                date = self._get_last_day_of_month(spread_date)
                amount = self._compute_board_amount(
                    sequence, unposted_amount, number_of_periods, date
                )
                amount = self.currency_id.round(amount)
                rounding = self.currency_id.rounding
                if float_is_zero(amount, precision_rounding=rounding):
                    continue
                unposted_amount -= amount
                vals = {
                    "amount": amount,
                    "spread_id": self.id,
                    "name": self._get_spread_entry_name(sequence),
                    "date": date,
                }
                commands.append((0, False, vals))

                spread_date = self._next_line_date(month_day, spread_date)

        self.write({"line_ids": commands})
        invoice_type_selection = dict(
            self.fields_get(allfields=["invoice_type"])["invoice_type"]["selection"]
        )[self.invoice_type]
        msg_body = _("Spread table '%s' created.") % invoice_type_selection
        self.message_post(body=msg_body)

    def _get_number_of_periods(self, month_day):
        """Calculates the number of spread lines."""
        self.ensure_one()
        return self.period_number + 1 if month_day != 1 else self.period_number

    @staticmethod
    def _get_first_day_of_month(spread_date):
        return spread_date + relativedelta(day=1)

    @staticmethod
    def _get_last_day_of_month(spread_date):
        return spread_date + relativedelta(day=31)

    def _get_spread_start_date(self, period_type, spread_end_date):
        self.ensure_one()
        spread_start_date = spread_end_date + relativedelta(days=1)
        if period_type == "month":
            spread_start_date = spread_end_date + relativedelta(day=1)
        elif period_type == "quarter":
            spread_start_date = spread_start_date - relativedelta(months=3)
        elif period_type == "year":
            spread_start_date = spread_start_date - relativedelta(years=1)
        spread_start_date = self._get_first_day_of_month(spread_start_date)
        spread_start_date = max(spread_start_date, self.spread_date)
        return spread_start_date

    def _get_spread_end_date(self, period_type, period_number, spread_start_date):
        self.ensure_one()
        spread_end_date = spread_start_date
        number_of_periods = (
            period_number if spread_start_date.day != 1 else period_number - 1
        )
        if period_type == "month":
            spread_end_date = spread_start_date + relativedelta(
                months=number_of_periods
            )
        elif period_type == "quarter":
            months = number_of_periods * 3
            spread_end_date = spread_start_date + relativedelta(months=months)
        elif period_type == "year":
            spread_end_date = spread_start_date + relativedelta(years=number_of_periods)
        # calculate by days and not first day of month should compute residual day only
        if self.days_calc and spread_end_date.day != 1:
            spread_end_date = spread_end_date - timedelta(days=1)
        else:
            spread_end_date = self._get_last_day_of_month(spread_end_date)
        return spread_end_date

    def _get_amount_per_day(self, amount):
        self.ensure_one()
        spread_start_date = self.spread_date
        spread_end_date = self._get_spread_end_date(
            self.period_type, self.period_number, spread_start_date
        )
        number_of_days = (spread_end_date - spread_start_date).days + 1
        return amount / number_of_days

    def _compute_board_amount(
        self, sequence, amount, number_of_periods, spread_end_date
    ):
        """Calculates the amount for the spread lines."""
        self.ensure_one()
        amount_to_spread = self.total_amount
        period = self.period_number
        if sequence != number_of_periods:
            amount = amount_to_spread / period
            if sequence == 1:
                date = self.spread_date
                month_days = calendar.monthrange(date.year, date.month)[1]
                days = month_days - date.day + 1
                amount = (amount_to_spread / period) / month_days * days
            if self.days_calc:
                spread_start_date = self._get_spread_start_date(
                    self.period_type, spread_end_date
                )
                days = (spread_end_date - spread_start_date).days + 1
                amount = self._get_amount_per_day(amount_to_spread) * days
        return amount

    def compute_spread_board(self):
        """Checks whether the spread lines should be calculated.
        In case checks pass, invoke "def _compute_spread_board()" method.
        """
        for spread in self.filtered(lambda s: s.total_amount):
            spread._compute_spread_board()

    def action_recalculate_spread(self):
        """Recalculate spread"""
        self.ensure_one()
        spread_lines = self.mapped("line_ids").filtered("move_id")
        spread_lines.unlink_move()
        self.compute_spread_board()
        self.env["account.spread.line"]._create_entries()

    def action_undo_spread(self):
        """Undo spreading: Remove all created moves"""
        self.ensure_one()
        self.mapped("line_ids").filtered("move_id").unlink_move()
        self.mapped("line_ids").unlink()

    def action_unlink_invoice_line(self):
        """Unlink the invoice line from the spread board"""
        self.ensure_one()
        if self.invoice_id.state != "draft":
            msg = _("Cannot unlink invoice lines if the invoice is validated")
            raise UserError(msg)
        self._action_unlink_invoice_line()

    def _action_unlink_invoice_line(self):
        self.mapped("line_ids.move_id.line_ids").remove_move_reconcile()
        self._message_post_unlink_invoice_line()
        self.write({"invoice_line_ids": [(5, 0, 0)]})

    def _message_post_unlink_invoice_line(self):
        for spread in self:
            inv_link = (
                "<a href=# data-oe-model=account.move "
                "data-oe-id=%d>%s</a>" % (spread.invoice_id.id, _("Invoice"))
            )
            msg_body = _(
                "Unlinked invoice line '%(spread_line_name)s' (view %(inv_link)s)."
            ) % {
                "spread_line_name": spread.invoice_line_id.name,
                "inv_link": inv_link,
            }
            spread.message_post(body=msg_body)
            spread_link = (
                "<a href=# data-oe-model=account.spread "
                "data-oe-id=%d>%s</a>" % (spread.id, _("Spread"))
            )
            msg_body = _("Unlinked '%(spread_link)s' (invoice line %(inv_line)s).") % {
                "spread_link": spread_link,
                "inv_line": spread.invoice_line_id.name,
            }
            spread.invoice_id.message_post(body=msg_body)

    def unlink(self):
        if self.filtered(lambda s: s.invoice_line_id):
            err_msg = _("Cannot delete spread(s) that are linked to an invoice line.")
            raise UserError(err_msg)
        if self.mapped("line_ids.move_id").filtered(lambda m: m.state == "posted"):
            err_msg = _("Cannot delete spread(s): there are posted Journal Entries.")
            raise ValidationError(err_msg)
        return super().unlink()

    def reconcile_spread_moves(self):
        for spread in self:
            spread._reconcile_spread_moves()

    def _reconcile_spread_moves(self, created_moves=False):
        """Reconcile spread moves if possible"""
        self.ensure_one()

        spread_mls = self.line_ids.mapped("move_id.line_ids")
        if created_moves:
            spread_mls |= created_moves.mapped("line_ids")

        account = self.invoice_line_id.account_id
        mls_to_reconcile = spread_mls.filtered(lambda l: l.account_id == account)

        if mls_to_reconcile:
            do_reconcile = mls_to_reconcile + self.invoice_line_id
            do_reconcile.remove_move_reconcile()
            # ensure to reconcile only posted items
            do_reconcile = do_reconcile.filtered(lambda l: l.move_id.state == "posted")
            do_reconcile._check_spread_reconcile_validity()
            do_reconcile.reconcile()

    def create_all_moves(self):
        for line in self.mapped("line_ids").filtered(lambda l: not l.move_id):
            line.create_move()

    def _post_spread_moves(self, moves):
        self.ensure_one()
        moves = moves.filtered(lambda l: l.state != "posted")
        if not moves:
            return
        ctx = dict(self.env.context, skip_unique_sequence_number=True)
        if self.company_id.force_move_auto_post or self.move_line_auto_post:
            moves.with_context(**ctx).action_post()

    @api.depends("debit_account_id.deprecated", "credit_account_id.deprecated")
    def _compute_deprecated_accounts(self):
        for spread in self:
            spread.is_debit_account_deprecated = spread.debit_account_id.deprecated
            spread.is_credit_account_deprecated = spread.credit_account_id.deprecated

    def open_reconcile_view(self):
        action_name = "account_spread_cost_revenue.action_account_moves_all_spread"
        [action] = self.env.ref(action_name).read()
        action["domain"] = [("id", "in", [])]
        spread_mls = self.line_ids.mapped("move_id.line_ids")
        spread_mls = spread_mls.filtered(lambda m: m.reconciled)
        if spread_mls:
            domain = [("id", "in", spread_mls.ids + [self.invoice_line_id.id])]
            action["domain"] = domain
        return action
