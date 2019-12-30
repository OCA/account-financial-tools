# Copyright 2019 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveBudgetLine(models.Model):
    _name = "account.move.budget.line"
    _description = "Account Move Budget Line"
    _order = "date desc, id desc"

    budget_id = fields.Many2one(
        comodel_name="account.move.budget",
        string="Budget",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Label")
    debit = fields.Monetary(default=0.0, currency_field="company_currency_id")
    credit = fields.Monetary(default=0.0, currency_field="company_currency_id")
    balance = fields.Monetary(
        compute="_compute_store_balance",
        store=True,
        currency_field="company_currency_id",
        help="Technical field holding the debit - "
        "credit in order to open meaningful "
        "graph views from reports",
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        readonly=True,
        help="Utility field to express amount currency",
        store=True,
    )
    account_id = fields.Many2one(
        "account.account",
        string="Account",
        required=True,
        index=True,
        ondelete="cascade",
        domain=[("deprecated", "=", False)],
        default=lambda self: self._context.get("account_id", False),
    )
    date = fields.Date(string="Date", index=True, required=True)
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account"
    )
    company_id = fields.Many2one(
        "res.company",
        related="account_id.company_id",
        string="Company",
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", string="Partner", ondelete="restrict")

    @api.depends("debit", "credit")
    def _compute_store_balance(self):
        for line in self:
            line.balance = line.debit - line.credit

    @api.constrains("date")
    def _constraint_date(self):
        for rec in self:
            if rec.budget_id.date_from > rec.date or rec.budget_id.date_to < rec.date:
                raise ValidationError(_("The date must be within the budget period."))
