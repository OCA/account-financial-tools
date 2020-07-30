# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountSpreadTemplate(models.Model):
    _name = 'account.spread.template'
    _description = 'Account Spread Template'

    name = fields.Char(required=True)
    spread_type = fields.Selection([
        ('sale', 'Customer'),
        ('purchase', 'Supplier')],
        default='sale',
        required=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        required=True)
    spread_journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True)
    use_invoice_line_account = fields.Boolean(
        string="Invoice account as spread account",
        help="Use invoice line's account as Balance sheet / spread account.\n"
        "In this case, user need to select expense/revenue account too.")
    spread_account_id = fields.Many2one(
        'account.account',
        string='Spread Balance Sheet Account',
        required=False)
    exp_rev_account_id = fields.Many2one(
        'account.account',
        string='Expense/Revenue Account',
        help="Optional account to overwrite the existing expense/revenue "
             "account")
    period_number = fields.Integer(
        string='Number of Repetitions',
        help="Define the number of spread lines")
    period_type = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year')],
        help="Period length for the entries")
    start_date = fields.Date()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'company_id' not in fields:
            company_id = self.env.user.company_id.id
        else:
            company_id = res['company_id']
        default_journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', company_id)],
            limit=1)
        if 'spread_journal_id' not in res and default_journal:
            res['spread_journal_id'] = default_journal.id
        return res

    @api.onchange('spread_type', 'company_id')
    def onchange_spread_type(self):
        company = self.company_id
        if self.spread_type == 'sale':
            account = company.default_spread_revenue_account_id
            journal = company.default_spread_revenue_journal_id
        else:
            account = company.default_spread_expense_account_id
            journal = company.default_spread_expense_journal_id
        if account:
            self.spread_account_id = account
        if journal:
            self.spread_journal_id = journal

    @api.onchange('use_invoice_line_account')
    def _onchange_user_invoice_line_account(self):
        self.exp_rev_account_id = False

    def _prepare_spread_from_template(self, spread_account_id=False):
        self.ensure_one()
        company = self.company_id
        spread_vals = {
            'name': self.name,
            'template_id': self.id,
            'journal_id': self.spread_journal_id.id,
            'use_invoice_line_account': self.use_invoice_line_account,
            'company_id': company.id,
        }

        account_id = spread_account_id or self.spread_account_id.id
        if self.spread_type == 'sale':
            invoice_type = 'out_invoice'
            spread_vals['debit_account_id'] = account_id
        else:
            invoice_type = 'in_invoice'
            spread_vals['credit_account_id'] = account_id

        if self.period_number:
            spread_vals['period_number'] = self.period_number
        if self.period_type:
            spread_vals['period_type'] = self.period_type
        if self.start_date:
            spread_vals['spread_date'] = self.start_date

        spread_vals['invoice_type'] = invoice_type
        return spread_vals
