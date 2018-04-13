# Copyright 2018 Ahmed Yousif
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, tools

class AccountLoanReport(models.Model):
    _name = "account.loan.report"
    _description = "Loans Analysis"
    _auto = False

    name = fields.Char(string='Loan', required=False, readonly=True)
    description = fields.Char(string='Description', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Lender', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    periods = fields.Integer(string='# of Loan Periods', readonly=True)
    method_period = fields.Integer(string='Time Between Loan Periods', readonly=True)
    rate = fields.Float(string='Loan Rate', readonly=True)
    pending_principal_amount = fields.Float(string='Amount of Pending Principal', readonly=True)
    payment_amount = fields.Float(string='Amount of Payment', readonly=True)
    interests_amount = fields.Float(string='Amount of Interests', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancelled', 'Cancelled'), ('close', 'Close')], string='Status', readonly=True)
    loan_type = fields.Selection([('fixed-annuity', 'Fixed Annuity'), ('fixed-principal', 'Fixed Principal'), ('interest', 'Only interest')], readonly=True)
    start_date = fields.Date(string='Loan Date', readonly=True)
    rate_type = fields.Selection([('napr', 'Nominal APR'), ('ear', 'EAR'), ('real', 'Real rate')], readonly=True)
    loan_amount = fields.Float(string='Loan Amount', readonly=True)
    short_term_loan_account_id = fields.Many2one('account.account', string='Short term account', readonly=True)
    long_term_loan_account_id = fields.Many2one('account.account', string='Long term account', readonly=True)
    interest_expenses_account_id = fields.Many2one('account.account', string='Interests account', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'account_loan_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW account_loan_report AS (
                SELECT
                    al.id as id,
                    al.name as name,
                    al.description as description,
                    al.partner_id as partner_id,
                    al.company_id as company_id,
                    al.periods as periods,
                    al.method_period as method_period,
                    al.rate as rate,
                    al.loan_amount as loan_amount,
                    SUM(ll.payment_amount) as payment_amount,
                    SUM(ll.interests_amount) as interests_amount,
                    (al.loan_amount - SUM(ll.payment_amount) + SUM(ll.interests_amount)) as pending_principal_amount,
                    al.state as state,
                    al.loan_type as loan_type,
                    al.start_date as start_date,
                    al.rate_type as rate_type,
                    al.short_term_loan_account_id as short_term_loan_account_id,
                    al.long_term_loan_account_id as long_term_loan_account_id,
                    al.interest_expenses_account_id as interest_expenses_account_id
                FROM
                    account_loan as al
                    Left JOIN account_loan_line as ll on (ll.loan_id=al.id AND (ll.has_moves = True OR ll.has_invoices = True))
                GROUP BY
                    al.name,
                    al.description,
                    al.partner_id,
                    al.company_id,
                    al.state,
                    al.loan_type,
                    al.start_date,
                    al.rate_type,
                    al.short_term_loan_account_id,
                    al.long_term_loan_account_id,
                    al.interest_expenses_account_id,
                    al.id
        )""")