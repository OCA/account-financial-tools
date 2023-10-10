# Copyright 2018-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountSpreadTemplate(models.Model):
    _name = "account.spread.template"
    _inherit = "analytic.mixin"
    _description = "Account Spread Template"

    name = fields.Char(required=True)
    spread_type = fields.Selection(
        [("sale", "Customer"), ("purchase", "Supplier")], default="sale", required=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    spread_journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        compute="_compute_spread_journal",
        readonly=False,
        store=True,
        required=True,
    )
    use_invoice_line_account = fields.Boolean(
        string="Invoice account as spread account",
        help="Use invoice line's account as Balance sheet / spread account.\n"
        "In this case, user need to select expense/revenue account too.",
    )
    spread_account_id = fields.Many2one(
        "account.account",
        string="Spread Balance Sheet Account",
        compute="_compute_spread_account",
        readonly=False,
        store=True,
        required=False,
    )
    exp_rev_account_id = fields.Many2one(
        "account.account",
        string="Expense/Revenue Account",
        help="Optional account to overwrite the existing expense/revenue account",
    )
    period_number = fields.Integer(
        string="Number of Repetitions", help="Define the number of spread lines"
    )
    period_type = fields.Selection(
        [("month", "Month"), ("quarter", "Quarter"), ("year", "Year")],
        help="Period length for the entries",
    )
    start_date = fields.Date()
    days_calc = fields.Boolean(
        string="Calculate by days",
        default=False,
        help="Use number of days to calculate amount",
    )
    auto_spread = fields.Boolean(
        string="Auto assign template on invoice validate",
        help="If checked, provide option to auto create spread during "
        "invoice validation, based on product/account/analytic in invoice line.",
    )
    auto_spread_ids = fields.One2many(
        comodel_name="account.spread.template.auto",
        string="Auto Spread On",
        inverse_name="template_id",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if not res.get("company_id"):
            res["company_id"] = self.env.company.id
        if "spread_journal_id" not in res:
            default_journal = self.env["account.spread"].default_journal(
                res["company_id"]
            )
            if default_journal:
                res["spread_journal_id"] = default_journal.id
        return res

    @api.constrains("auto_spread", "auto_spread_ids")
    def _check_product_account(self):
        for rec in self.filtered("auto_spread"):
            for line in rec.auto_spread_ids:
                if not line.product_id and not line.account_id:
                    raise UserError(
                        _(
                            "Please select product and/or account "
                            "on auto spread options"
                        )
                    )

    @api.depends("spread_type", "company_id")
    def _compute_spread_journal(self):
        for spread in self:
            company = spread.company_id
            if spread.spread_type == "sale":
                journal = company.default_spread_revenue_journal_id
            else:
                journal = company.default_spread_expense_journal_id
            if journal:
                spread.spread_journal_id = journal

    @api.depends("spread_type", "company_id")
    def _compute_spread_account(self):
        for spread in self:
            company = spread.company_id
            if spread.spread_type == "sale":
                account = company.default_spread_revenue_account_id
            else:
                account = company.default_spread_expense_account_id
            if account:
                spread.spread_account_id = account

    @api.onchange("use_invoice_line_account")
    def _onchange_user_invoice_line_account(self):
        self.exp_rev_account_id = False

    def _prepare_spread_from_template(self, spread_account_id=False):
        self.ensure_one()
        company = self.company_id
        spread_vals = {
            "name": self.name,
            "template_id": self.id,
            "journal_id": self.spread_journal_id.id,
            "use_invoice_line_account": self.use_invoice_line_account,
            "days_calc": self.days_calc,
            "company_id": company.id,
        }

        account_id = spread_account_id or self.spread_account_id.id
        if self.spread_type == "sale":
            invoice_type = "out_invoice"
            spread_vals["debit_account_id"] = account_id
        else:
            invoice_type = "in_invoice"
            spread_vals["credit_account_id"] = account_id

        if self.period_number:
            spread_vals["period_number"] = self.period_number
        if self.period_type:
            spread_vals["period_type"] = self.period_type
        if self.start_date:
            spread_vals["spread_date"] = self.start_date

        spread_vals["invoice_type"] = invoice_type
        return spread_vals


class AccountSpreadTemplateAuto(models.Model):
    _name = "account.spread.template.auto"
    _inherit = "analytic.mixin"
    _description = "Auto create spread, based on product/account/analytic"

    template_id = fields.Many2one(
        comodel_name="account.spread.template",
        string="Spread Template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="template_id.company_id",
        store=True,
    )
    name = fields.Char(
        required=True,
        default="/",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
    )
