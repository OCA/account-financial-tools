# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountCashDeposit(models.Model):
    _name = "account.cash.deposit"
    _description = "Cash Deposit/Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Reference",
        size=64,
        readonly=True,
        default=lambda self: _("New"),
        copy=False,
    )
    operation_type = fields.Selection(
        [
            ("deposit", "Cash Deposit"),
            ("order", "Cash Order"),
        ],
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        "account.cash.deposit.line",
        "parent_id",
        string="Lines",
    )
    order_date = fields.Date(
        default=fields.Date.context_today,
    )
    date = fields.Date(
        tracking=True,
        copy=False,
        help="Used as date for the journal entry.",
    )
    cash_journal_id = fields.Many2one(
        "account.journal",
        string="Cash Box",
        domain="[('company_id', '=', company_id), ('type', '=', 'cash')]",
        required=True,
        check_company=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),  # step only for orders, not for deposits
            ("done", "Done"),
        ],
        string="Status",
        default="draft",
        readonly=True,
        tracking=True,
    )
    move_id = fields.Many2one(
        "account.move",
        string="Journal Entry",
        readonly=True,
        check_company=True,
    )
    bank_journal_id = fields.Many2one(
        "account.journal",
        string="Bank Account",
        required=True,
        domain="[('company_id', '=', company_id), ('type', '=', 'bank'), "
        "('bank_account_id', '!=', False)]",
        check_company=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        tracking=True,
    )
    coin_amount = fields.Monetary(
        string="Loose Coin Amount",
        currency_field="currency_id",
        tracking=True,
        help="If your bank has a coin counting machine, enter the total amount "
        "of coins counted by the machine instead of creating a line for each type "
        "of coin.",
    )
    total_amount = fields.Monetary(
        compute="_compute_total_amount",
        precompute=True,
        store=True,
        currency_field="currency_id",
        tracking=True,
    )
    is_reconcile = fields.Boolean(
        compute="_compute_is_reconcile", store=True, string="Reconciled"
    )
    notes = fields.Text()

    _sql_constraints = [
        (
            "name_company_unique",
            "unique(company_id, name)",
            "A cash deposit/order with this reference already exists in this company.",
        ),
        (
            "coin_amount_positive",
            "CHECK(coin_amount >= 0)",
            "The loose coin amount must be positive or null.",
        ),
    ]

    @api.constrains("cash_journal_id", "currency_id")
    def _check_deposit(self):
        for rec in self:
            if rec.currency_id and rec.cash_journal_id:
                if (
                    rec.cash_journal_id.currency_id
                    and rec.currency_id != rec.cash_journal_id.currency_id
                ) or (
                    not rec.cash_journal_id.currency_id
                    and rec.currency_id != rec.company_id.currency_id
                ):
                    raise ValidationError(
                        _(
                            "On %(deposit)s, the cash journal %(cash_journal)s is not "
                            "in the selected currency %(currency)s."
                        )
                        % {
                            "deposit": rec.display_name,
                            "cash_journal": rec.cash_journal_id.display_name,
                            "currency": rec.currency_id.name,
                        }
                    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ajo = self.env["account.journal"]
        company = self.env.company
        currency = company.currency_id
        # pre-set cash_journal_id and bank_journal_id if there is only one
        domain = [("company_id", "=", company.id)]
        cash_journals = ajo.search(
            domain
            + [
                ("type", "=", "cash"),
                "|",
                ("currency_id", "=", False),
                ("currency_id", "=", currency.id),
            ]
        )
        if len(cash_journals) == 1:
            res["cash_journal_id"] = cash_journals.id
        bank_journals = ajo.search(
            domain + [("type", "=", "bank"), ("bank_account_id", "!=", False)]
        )
        if len(bank_journals) == 1:
            res["bank_journal_id"] = bank_journals.id
        res.update(
            {
                "company_id": company.id,
                "currency_id": currency.id,
            }
        )
        if res.get("operation_type"):
            cash_units = self.env["cash.unit"].search(
                [
                    ("auto_create", "in", ("both", res["operation_type"])),
                    ("currency_id", "=", currency.id),
                ]
            )
            res["line_ids"] = [
                Command.create({"cash_unit_id": cu.id}) for cu in cash_units
            ]
        return res

    @api.depends("line_ids.subtotal", "coin_amount")
    def _compute_total_amount(self):
        # With precompute=True, we can't use read_group() any more,
        # because it won't work with NewID
        for rec in self:
            total_amount = rec.coin_amount
            for line in rec.line_ids:
                total_amount += line.subtotal
            rec.total_amount = total_amount

    @api.depends("move_id.line_ids.reconciled", "company_id")
    def _compute_is_reconcile(self):
        for rec in self:
            reconcile = False
            if rec.move_id:
                for line in rec.move_id.line_ids:
                    if (
                        line.account_id.id != rec.cash_journal_id.default_account_id.id
                        and line.reconciled
                    ):
                        reconcile = True
            rec.is_reconcile = reconcile

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    _("The %s is not in draft state, so you cannot delete it.")
                    % rec.display_name
                )
        return super().unlink()

    def backtodraft(self):
        for rec in self:
            if rec.move_id:
                if rec.is_reconcile:
                    raise UserError(
                        _("%s has already been credited/debited on the bank account.")
                        % rec.display_name
                    )
                move = rec.move_id
                if move.state == "posted":
                    move.button_draft()
                move.with_context(force_delete=True).unlink()
            rec.write({"state": "draft"})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                if (
                    vals.get("operation_type") == "order"
                    or self._context.get("default_operation_type") == "order"
                ):
                    vals["name"] = (
                        self.env["ir.sequence"]
                        .with_company(vals.get("company_id"))
                        .next_by_code("account.cash.order", vals.get("order_date"))
                    )
                else:
                    vals["name"] = (
                        self.env["ir.sequence"]
                        .with_company(vals.get("company_id"))
                        .next_by_code("account.cash.deposit")
                    )
        return super().create(vals_list)

    @api.depends("operation_type", "name")
    def _compute_display_name(self):
        type2label = dict(
            self.fields_get("operation_type", "selection")["operation_type"][
                "selection"
            ]
        )
        for rec in self:
            rec.display_name = " ".join([type2label[rec.operation_type], rec.name])

    def confirm_order(self):
        self.ensure_one()
        assert self.operation_type == "order", "Wrong operation type"
        self._del_empty_lines()
        self.write({"state": "confirmed"})

    def _del_empty_lines(self, raise_if_empty=True):
        self.ensure_one()
        self.line_ids.filtered(lambda x: x.qty == 0).unlink()
        if raise_if_empty and self.currency_id.is_zero(self.total_amount):
            raise UserError(_("The total amount of %s is zero.") % self.display_name)

    def _prepare_account_move(self, vals):
        self.ensure_one()
        date = vals.get("date") or self.date
        op_type = self.operation_type
        total_amount_comp_cur = self.currency_id._convert(
            self.total_amount, self.company_id.currency_id, self.company_id, date
        )
        if not self.company_id.transfer_account_id:
            raise UserError(_("The Inter-Banks Transfer Account is not configured."))
        bank_account_id = self.company_id.transfer_account_id.id

        cash_debit = cash_credit = bank_debit = bank_credit = 0.0
        if op_type == "deposit":
            cash_credit = total_amount_comp_cur
            bank_debit = total_amount_comp_cur
        else:
            cash_debit = total_amount_comp_cur
            bank_credit = total_amount_comp_cur
        # Cash move line
        cash_vals = {
            "account_id": self.cash_journal_id.default_account_id.id,
            "partner_id": False,
            "debit": cash_debit,
            "credit": cash_credit,
            "currency_id": self.currency_id.id,
            "amount_currency": self.total_amount * (op_type == "deposit" and -1 or 1),
        }
        # Bank move line
        bank_vals = {
            "account_id": bank_account_id,
            "partner_id": False,
            "debit": bank_debit,
            "credit": bank_credit,
            "currency_id": self.currency_id.id,
            "amount_currency": self.total_amount * (op_type == "deposit" and 1 or -1),
        }
        move_vals = {
            "journal_id": self.cash_journal_id.id,
            "date": date,
            "ref": self.display_name,
            "company_id": self.company_id.id,
            "line_ids": [Command.create(cash_vals), Command.create(bank_vals)],
        }
        return move_vals

    def _prepare_validate(self, force_date=None):
        vals = {"state": "done"}
        if force_date:
            vals["date"] = force_date
        elif not self.date:
            vals["date"] = fields.Date.context_today(self)
        return vals

    def validate(self, force_date=None):
        self.ensure_one()
        self._del_empty_lines()
        vals = self._prepare_validate(force_date=force_date)
        move_vals = self._prepare_account_move(vals)
        move = self.env["account.move"].create(move_vals)
        move.action_post()
        vals["move_id"] = move.id
        self.write(vals)

    @api.onchange("currency_id")
    def currency_change(self):
        if self.currency_id and self.operation_type:
            line_obj = self.env["account.cash.deposit.line"]
            new_lines = self.env["account.cash.deposit.line"]
            cash_units = self.env["cash.unit"].search(
                [
                    ("auto_create", "in", ("both", self.operation_type)),
                    ("currency_id", "=", self.currency_id.id),
                ]
            )
            for cunit in cash_units:
                new_lines += line_obj.new({"cash_unit_id": cunit.id})
            self.line_ids = new_lines
            domain = [("company_id", "=", self.company_id.id), ("type", "=", "cash")]
            if self.currency_id == self.company_id.currency_id:
                cash_journals = self.env["account.journal"].search(
                    domain
                    + [
                        "|",
                        ("currency_id", "=", False),
                        ("currency_id", "=", self.currency_id.id),
                    ]
                )
                if len(cash_journals) == 1:
                    self.cash_journal_id = cash_journals.id
                else:
                    self.cash_journal_id = False
            else:
                cash_journals = self.env["account.journal"].search(
                    domain + [("currency_id", "=", self.currency_id.id)]
                )
                if len(cash_journals) == 1:
                    self.cash_journal_id = cash_journals.id
                else:
                    self.cash_journal_id = False


class AccountCashDepositLine(models.Model):
    _name = "account.cash.deposit.line"
    _description = "Cash Deposit Lines"
    _order = "tree_order desc"

    parent_id = fields.Many2one("account.cash.deposit", ondelete="cascade")
    qty = fields.Integer(string="Quantity")
    cash_unit_id = fields.Many2one(
        "cash.unit", required=True, domain="[('currency_id', '=', currency_id)]"
    )
    tree_order = fields.Float(related="cash_unit_id.tree_order", store=True)
    subtotal = fields.Monetary(compute="_compute_subtotal", store=True, precompute=True)
    currency_id = fields.Many2one(related="parent_id.currency_id", store=True)

    _sql_constraints = [
        ("qty_positive", "CHECK(qty >= 0)", "The quantity must be positive or null."),
        (
            "cash_unit_unique",
            "unique(cash_unit_id, parent_id)",
            "A line already exists for this cash unit.",
        ),
    ]

    @api.constrains("currency_id", "cash_unit_id")
    def _check_lines(self):
        for line in self:
            if (
                line.currency_id
                and line.cash_unit_id
                and line.currency_id != line.cash_unit_id.currency_id
            ):
                raise ValidationError(
                    _(
                        "You must delete cash lines that are linked to a currency "
                        "other than %s."
                    )
                    % line.currency_id.name
                )

    @api.depends("cash_unit_id", "qty")
    def _compute_subtotal(self):
        for line in self:
            subtotal = 0
            if line.cash_unit_id:
                subtotal = line.cash_unit_id.total_value * line.qty
            line.subtotal = subtotal
