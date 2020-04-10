# Copyright 2012-2016 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountCheckDeposit(models.Model):
    _name = "account.check.deposit"
    _description = "Account Check Deposit"
    _order = "deposit_date desc"

    @api.depends(
        "company_id",
        "currency_id",
        "check_payment_ids.debit",
        "check_payment_ids.amount_currency",
        "move_id.line_ids.reconciled",
    )
    def _compute_check_deposit(self):
        for deposit in self:
            total = 0.0
            count = 0
            reconcile = False
            currency_none_same_company_id = False
            if deposit.company_id.currency_id != deposit.currency_id:
                currency_none_same_company_id = deposit.currency_id.id
            for line in deposit.check_payment_ids:
                count += 1
                if currency_none_same_company_id:
                    total += line.amount_currency
                else:
                    total += line.debit
            if deposit.move_id:
                for line in deposit.move_id.line_ids:
                    if line.debit > 0 and line.reconciled:
                        reconcile = True
            deposit.total_amount = total
            deposit.is_reconcile = reconcile
            deposit.currency_none_same_company_id = currency_none_same_company_id
            deposit.check_count = count

    name = fields.Char(string="Name", size=64, readonly=True, default="/")
    check_payment_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="check_deposit_id",
        string="Check Payments",
        states={"done": [("readonly", "=", True)]},
    )
    deposit_date = fields.Date(
        string="Deposit Date",
        required=True,
        states={"done": [("readonly", "=", True)]},
        default=fields.Date.context_today,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain=[("type", "=", "bank"), ("bank_account_id", "=", False)],
        required=True,
        states={"done": [("readonly", "=", True)]},
    )
    journal_default_account_id = fields.Many2one(
        comodel_name="account.account",
        related="journal_id.default_debit_account_id",
        string="Default Debit Account of the Journal",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        states={"done": [("readonly", "=", True)]},
    )
    currency_none_same_company_id = fields.Many2one(
        comodel_name="res.currency",
        compute="_compute_check_deposit",
        store=True,
        string="Currency (False if same as company)",
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done")],
        string="Status",
        default="draft",
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move", string="Journal Entry", readonly=True
    )
    bank_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Bank Account",
        required=True,
        domain="[('company_id', '=', company_id), ('type', '=', 'bank'), "
        "('bank_account_id', '!=', False)]",
        states={"done": [("readonly", "=", True)]},
    )
    line_ids = fields.One2many(
        comodel_name="account.move.line",
        related="move_id.line_ids",
        string="Lines",
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        states={"done": [("readonly", "=", True)]},
        default=lambda self: self.env.company,
    )
    total_amount = fields.Float(
        compute="_compute_check_deposit",
        string="Total Amount",
        readonly=True,
        store=True,
        digits="Account",
    )
    check_count = fields.Integer(
        compute="_compute_check_deposit",
        readonly=True,
        store=True,
        string="Number of Checks",
    )
    is_reconcile = fields.Boolean(
        compute="_compute_check_deposit", readonly=True, store=True, string="Reconcile"
    )

    @api.constrains("currency_id", "check_payment_ids", "company_id")
    def _check_deposit(self):
        for deposit in self:
            deposit_currency = deposit.currency_id
            if deposit_currency == deposit.company_id.currency_id:
                for line in deposit.check_payment_ids:
                    if line.currency_id:
                        raise ValidationError(
                            _(
                                "The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s."
                            )
                            % (
                                line.debit,
                                line.ref or "",
                                line.currency_id.name,
                                deposit_currency.name,
                            )
                        )
            else:
                for line in deposit.check_payment_ids:
                    if line.currency_id != deposit_currency:
                        raise ValidationError(
                            _(
                                "The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s."
                            )
                            % (
                                line.debit,
                                line.ref or "",
                                line.currency_id.name,
                                deposit_currency.name,
                            )
                        )

    def unlink(self):
        for deposit in self:
            if deposit.state == "done":
                raise UserError(
                    _(
                        "The deposit '%s' is in valid state, so you must "
                        "cancel it before deleting it."
                    )
                    % deposit.name
                )
        return super(AccountCheckDeposit, self).unlink()

    def backtodraft(self):
        for deposit in self:
            if deposit.move_id:
                # It will raise here if journal_id.update_posted = False
                deposit.move_id.button_cancel()
                for line in deposit.check_payment_ids:
                    if line.reconciled:
                        line.remove_move_reconcile()
                deposit.move_id.unlink()
            deposit.write({"state": "draft"})
        return True

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = (
                self.env["ir.sequence"]
                .with_context(ir_sequence_date=vals.get("deposit_date"))
                .next_by_code("account.check.deposit")
            )
        return super(AccountCheckDeposit, self).create(vals)

    @api.model
    def _prepare_account_move_vals(self, deposit):
        if deposit.company_id.check_deposit_offsetting_account == "bank_account":
            journal_id = deposit.bank_journal_id.id
        else:
            journal_id = deposit.journal_id.id
        move_vals = {
            "journal_id": journal_id,
            "date": deposit.deposit_date,
            "ref": _("Check Deposit %s") % deposit.name,
        }
        return move_vals

    @api.model
    def _prepare_move_line_vals(self, line):
        assert line.debit > 0, "Debit must have a value"
        return {
            "name": _("Check Deposit - Ref. Check %s") % line.ref,
            "credit": line.debit,
            "debit": 0.0,
            "account_id": line.account_id.id,
            "partner_id": line.partner_id.id,
            "currency_id": line.currency_id.id or False,
            "amount_currency": line.amount_currency * -1,
        }

    @api.model
    def _prepare_counterpart_move_lines_vals(
        self, deposit, total_debit, total_amount_currency
    ):
        company = deposit.company_id
        if not company.check_deposit_offsetting_account:
            raise UserError(
                _(
                    "You must configure the 'Check Deposit Offsetting Account' "
                    "on the Accounting Settings page"
                )
            )
        if company.check_deposit_offsetting_account == "bank_account":
            if not deposit.bank_journal_id.default_debit_account_id:
                raise UserError(
                    _("Missing 'Default Debit Account' on bank journal '%s'")
                    % deposit.bank_journal_id.name
                )
            account_id = deposit.bank_journal_id.default_debit_account_id.id
        elif company.check_deposit_offsetting_account == "transfer_account":
            if not company.check_deposit_transfer_account_id:
                raise UserError(
                    _(
                        "Missing 'Check Deposit Offsetting Account' on the "
                        "company '%s'."
                    )
                    % company.name
                )
            account_id = company.check_deposit_transfer_account_id.id
        return {
            "name": _("Check Deposit %s") % deposit.name,
            "debit": total_debit,
            "credit": 0.0,
            "account_id": account_id,
            "partner_id": False,
            "currency_id": deposit.currency_none_same_company_id.id or False,
            "amount_currency": total_amount_currency,
        }

    def validate_deposit(self):
        am_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        for deposit in self:
            move_vals = self._prepare_account_move_vals(deposit)
            move = am_obj.create(move_vals)
            total_debit = 0.0
            total_amount_currency = 0.0
            to_reconcile_lines = []
            for line in deposit.check_payment_ids:
                total_debit += line.debit
                total_amount_currency += line.amount_currency
                line_vals = self._prepare_move_line_vals(line)
                line_vals["move_id"] = move.id
                move_line = move_line_obj.with_context(
                    check_move_validity=False
                ).create(line_vals)
                to_reconcile_lines.append(line + move_line)

            # Create counter-part
            counter_vals = self._prepare_counterpart_move_lines_vals(
                deposit, total_debit, total_amount_currency
            )
            counter_vals["move_id"] = move.id
            move_line_obj.create(counter_vals)
            if deposit.company_id.check_deposit_post_move:
                move.post()

            deposit.write({"state": "done", "move_id": move.id})
            for reconcile_lines in to_reconcile_lines:
                reconcile_lines.reconcile()
        return True

    @api.onchange("company_id")
    def onchange_company_id(self):
        if self.company_id:
            bank_journals = self.env["account.journal"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("type", "=", "bank"),
                    ("bank_account_id", "!=", False),
                ]
            )
            if len(bank_journals) == 1:
                self.bank_journal_id = bank_journals[0]
        else:
            self.bank_journal_id = False

    @api.onchange("journal_id")
    def onchange_journal_id(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id
            else:
                self.currency_id = self.journal_id.company_id.currency_id

    def get_report(self):
        report = self.env.ref("account_check_deposit.report_account_check_deposit")
        action = report.report_action(self)
        return action
