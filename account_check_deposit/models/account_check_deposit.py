# Copyright 2012-2022 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# Copyright 2018-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountCheckDeposit(models.Model):
    _name = "account.check.deposit"
    _description = "Check Deposit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "deposit_date desc"
    _check_company_auto = True

    name = fields.Char(readonly=True, default=lambda self: _("New"), copy=False)
    check_payment_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="check_deposit_id",
        string="Check Payments",
    )
    deposit_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        copy=False,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Check Journal",
        domain="[('company_id', '=', company_id), ('type', '=', 'bank'), "
        "('bank_account_id', '=', False)]",
        required=True,
        check_company=True,
        tracking=True,
    )
    in_hand_check_account_id = fields.Many2one(
        comodel_name="account.account",
        compute="_compute_in_hand_check_account_id",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        compute="_compute_currency_id",
        store=True,
        precompute=True,
        readonly=False,
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done")],
        string="Status",
        default="draft",
        readonly=True,
        tracking=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
        readonly=True,
        check_company=True,
    )
    bank_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Bank Account",
        required=True,
        domain="[('company_id', '=', company_id), ('type', '=', 'bank'), "
        "('bank_account_id', '!=', False)]",
        check_company=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name="account.move.line",
        related="move_id.line_ids",
        string="Lines",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    total_amount = fields.Monetary(
        compute="_compute_check_deposit",
        store=True,
        currency_field="currency_id",
        tracking=True,
    )
    check_count = fields.Integer(
        compute="_compute_check_deposit",
        store=True,
        string="Number of Checks",
        tracking=True,
    )

    _sql_constraints = [
        (
            "name_company_unique",
            "unique(company_id, name)",
            "A check deposit with this reference already exists in this company.",
        )
    ]

    @api.depends(
        "company_id",
        "currency_id",
        "check_payment_ids.debit",
        "check_payment_ids.amount_currency",
        "move_id.line_ids.reconciled",
    )
    def _compute_check_deposit(self):
        rg_res = self.env["account.move.line"]._read_group(
            [("check_deposit_id", "in", self.ids)],
            groupby=["check_deposit_id"],
            aggregates=["amount_currency:sum", "debit:sum", "id:count"],
        )
        mapped_data = {
            deposit.id: {
                "debit": total_debit,
                "amount_currency": total_amount_currency,
                "count": line_count,
            }
            for (deposit, total_amount_currency, total_debit, line_count) in rg_res
        }

        for deposit in self:
            if deposit.company_id.currency_id != deposit.currency_id:
                total = mapped_data.get(deposit.id, {"amount_currency": 0.0})[
                    "amount_currency"
                ]
            else:
                total = mapped_data.get(deposit.id, {"debit": 0.0})["debit"]
            count = mapped_data.get(deposit.id, {"count": 0})["count"]
            deposit.total_amount = deposit.currency_id.round(total)
            deposit.check_count = count

    @api.depends("journal_id")
    def _compute_currency_id(self):
        for deposit in self:
            company = deposit.company_id
            deposit.currency_id = deposit.journal_id.currency_id or company.currency_id

    @api.depends("journal_id")
    def _compute_in_hand_check_account_id(self):
        for rec in self:
            account = rec.journal_id.inbound_payment_method_line_ids.filtered(
                lambda line: line.payment_method_id.code == "manual"
            ).payment_account_id
            rec.in_hand_check_account_id = account

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ajo = self.env["account.journal"]
        company_id = res.get("company_id")
        # pre-set journal_id and bank_journal_id is there is only one
        domain = [("company_id", "=", company_id), ("type", "=", "bank")]
        journals = ajo.search(domain + [("bank_account_id", "=", False)])
        if len(journals) == 1:
            res["journal_id"] = journals.id
        bank_journals = ajo.search(domain + [("bank_account_id", "!=", False)])
        if len(bank_journals) == 1:
            res["bank_journal_id"] = bank_journals.id
        return res

    @api.constrains("currency_id", "check_payment_ids")
    def _check_deposit(self):
        for deposit in self:
            deposit_currency = deposit.currency_id
            for line in deposit.check_payment_ids:
                if line.currency_id != deposit_currency:
                    raise ValidationError(
                        _(
                            "The check with amount %(amount)s and reference '%(ref)s' "
                            "is in currency %(check_currency)s but the deposit is in "
                            "currency %(deposit_currency)s.",
                            amount=line.debit,
                            ref=line.ref or "",
                            check_currency=line.currency_id.name,
                            deposit_currency=deposit_currency.name,
                        )
                    )

    def unlink(self):
        for deposit in self.filtered(lambda x: x.state == "done"):
            raise UserError(
                _(
                    "The deposit '%s' is in valid state, so you must "
                    "cancel it before deleting it."
                )
                % deposit.display_name
            )
        return super().unlink()

    def backtodraft(self):
        amlo = self.env["account.move.line"]
        for deposit in self:
            if deposit.move_id:
                move = deposit.move_id
                check_move_lines = amlo
                counterpart_move_line = amlo
                for move_line in move.line_ids:
                    if move_line.account_id.id == deposit.in_hand_check_account_id.id:
                        check_move_lines |= move_line
                    else:
                        counterpart_move_line |= move_line
                if counterpart_move_line.reconciled:
                    raise UserError(
                        _("Deposit '%s' has already been credited on the bank account.")
                        % deposit.display_name
                    )
                check_move_lines.remove_move_reconcile()
                if move.state == "posted":
                    move.button_cancel()
                move.with_context(force_delete=True).unlink()
            deposit.write({"state": "draft"})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "company_id" in vals:
                self = self.with_company(vals["company_id"])
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "account.check.deposit", vals.get("deposit_date")
                ) or _("New")
        return super().create(vals_list)

    def _prepare_move_vals(self):
        self.ensure_one()
        total_debit = 0.0
        total_amount_currency = 0.0
        for line in self.check_payment_ids:
            total_debit += line.debit
            total_amount_currency += line.amount_currency

        total_debit = self.company_id.currency_id.round(total_debit)
        total_amount_currency = self.currency_id.round(total_amount_currency)

        counterpart_account_id = False
        for line in self.bank_journal_id.inbound_payment_method_line_ids:
            if line.payment_method_id.code == "manual" and line.payment_account_id:
                counterpart_account_id = line.payment_account_id.id
                break
        if not counterpart_account_id:
            counterpart_account_id = (
                self.company_id.account_journal_payment_debit_account_id.id
            )
        if not counterpart_account_id:
            raise UserError(
                _("Missing 'Outstanding Receipts Account' on the company '%s'.")
                % self.company_id.display_name
            )

        vals = {
            "journal_id": self.journal_id.id,
            "date": self.deposit_date,
            "ref": _("Check Deposit %s") % self.name,
            "company_id": self.company_id.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "account_id": self.in_hand_check_account_id.id,
                        "partner_id": False,
                        "credit": total_debit,
                        "currency_id": self.currency_id.id,
                        "amount_currency": total_amount_currency * -1,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "account_id": counterpart_account_id,
                        "partner_id": False,
                        "debit": total_debit,
                        "currency_id": self.currency_id.id,
                        "amount_currency": total_amount_currency,
                    },
                ),
            ],
        }
        return vals

    def validate_deposit(self):
        am_obj = self.env["account.move"]
        for deposit in self:
            move = am_obj.create(deposit._prepare_move_vals())
            move.action_post()
            lines_to_rec = self.check_payment_ids + move.line_ids.filtered(
                lambda x: x.account_id.id == self.in_hand_check_account_id.id
            )
            lines_to_rec.reconcile()
            deposit.write({"state": "done", "move_id": move.id})

    def get_all_checks(self):
        self.ensure_one()
        if not self.in_hand_check_account_id:
            raise UserError(
                _(
                    "In the configuration of journal '%s', "
                    "in the 'Incoming Payments' tab, you must configure an "
                    "Outstanding Receipts Account for the payment method "
                    "'Manual (inbound)'."
                )
                % self.journal_id.display_name
            )
        all_pending_checks = self.env["account.move.line"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("reconciled", "=", False),
                ("account_id", "=", self.in_hand_check_account_id.id),
                ("debit", ">", 0),
                ("check_deposit_id", "=", False),
                ("currency_id", "=", self.currency_id.id),
                ("parent_state", "=", "posted"),
            ]
        )
        if all_pending_checks:
            self.message_post(body=_("Get All Received Checks"))
            all_pending_checks.write({"check_deposit_id": self.id})
        else:
            raise UserError(
                _(
                    "There are no received checks in account '%(account)s' in currency "
                    "'%(currency)s' that are not already in this check deposit.",
                    account=self.in_hand_check_account_id.display_name,
                    currency=self.currency_id.display_name,
                )
            )
