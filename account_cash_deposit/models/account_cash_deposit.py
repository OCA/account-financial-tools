# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountCashDeposit(models.Model):
    _name = "account.cash.deposit"
    _description = "Cash Deposit/Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Reference", size=64, readonly=True, default="/", copy=False
    )
    operation_type = fields.Selection(
        [
            ("deposit", "Cash Deposit"),
            ("order", "Cash Order"),
        ],
        required=True,
        string="Operation Type",
        readonly=True,
    )
    line_ids = fields.One2many(
        "account.cash.deposit.line",
        "parent_id",
        string="Lines",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )
    order_date = fields.Date(
        default=fields.Date.context_today,
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )
    date = fields.Date(
        string="Date",
        readonly=True,
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
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
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
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
        tracking=True,
    )
    total_amount = fields.Monetary(
        compute="_compute_total_amount",
        string="Total Amount",
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
        )
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
                            "On {deposit}, the cash journal {cash_journal} is not "
                            "in the selected currency {currency}."
                        ).format(
                            deposit=rec.display_name,
                            cash_journal=rec.cash_journal_id.display_name,
                            currency=rec.currency_id.name,
                        )
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
            res["line_ids"] = [(0, 0, {"cash_unit_id": cu.id}) for cu in cash_units]
        return res

    @api.depends("line_ids.subtotal")
    def _compute_total_amount(self):
        rg_res = self.env["account.cash.deposit.line"].read_group(
            [("parent_id", "in", self.ids)],
            ["parent_id", "subtotal"],
            ["parent_id"],
        )
        mapped_data = {x["parent_id"][0]: x["subtotal"] for x in rg_res}
        for rec in self:
            rec.total_amount = mapped_data.get(rec.id, 0)

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
                move = rec.move_id
                # It will raise here if journal_id.update_posted = False
                if move.state == "posted":
                    move.button_draft()
                move.unlink()
            rec.write({"state": "draft"})

    @api.model
    def create(self, vals):
        if "company_id" in vals:
            self = self.with_company(vals["company_id"])
        if vals.get("name", "/") == "/":
            if (
                vals.get("operation_type") == "order"
                or self._context.get("default_operation_type") == "order"
            ):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "account.cash.order", vals.get("order_date")
                )
            else:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "account.cash.deposit"
                )
        return super().create(vals)

    def name_get(self):
        res = []
        type2label = dict(
            self.fields_get("operation_type", "selection")["operation_type"][
                "selection"
            ]
        )
        for rec in self:
            res.append((rec.id, " ".join([type2label[self.operation_type], self.name])))
        return res

    def confirm_order(self):
        self.ensure_one()
        assert self.operation_type == "order", "Wrong operation type"
        self._del_empty_lines()
        self.write({"state": "confirmed"})

    def _del_empty_lines(self, raise_if_empty=True):
        self.ensure_one()
        self.line_ids.filtered(lambda x: x.qty == 0).unlink()
        if raise_if_empty and not self.line_ids:
            raise UserError(_("There are no non-zero lines on %s!") % self.display_name)

    def _prepare_account_move(self, vals):
        self.ensure_one()
        date = vals["date"]
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
            "line_ids": [(0, 0, cash_vals), (0, 0, bank_vals)],
        }
        return move_vals

    def _prepare_validate(self, force_date=None):
        vals = {"state": "done"}
        if force_date:
            vals["date"] = force_date
        else:
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

    def get_report(self):
        report = self.env.ref("account_cash_deposit.report_account_cash_deposit")
        action = report.with_context({"discard_logo_check": True}).report_action(self)
        return action


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
    subtotal = fields.Monetary(compute="_compute_subtotal", store=True)
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
