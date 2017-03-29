# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools
from odoo.tools.safe_eval import safe_eval

from ..models.financial_move import (
    FINANCIAL_STATE,
    FINANCIAL_TYPE
)


class FinancialCashflow(models.Model):
    _name = 'financial.cashflow'
    _auto = False
    _order = 'date_business_maturity, id'

    amount_cumulative_balance = fields.Monetary(
        string=u"Balance",
    )
    amount_debit = fields.Monetary(
        string=u"Debit",
    )
    amount_credit = fields.Monetary(
        string=u"Credit",
    )
    amount_paid = fields.Monetary(
        string=u"Paid",
    )
    state = fields.Selection(
        selection=FINANCIAL_STATE,
        string=u'Status',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Company',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Currency',
    )
    partner_id = fields.Many2one(
        string=u'Partner',
        comodel_name='res.partner',
    )
    document_number = fields.Char(
        string=u"Document Nº",
    )
    document_item = fields.Char(
        string=u"Document item",
    )
    date = fields.Date(
        string=u"Document date",
    )
    amount_total = fields.Monetary(
        string=u"Total",
    )
    date_maturity = fields.Date(
        string=u"Maturity",
    )
    financial_type = fields.Selection(
        selection=FINANCIAL_TYPE,
    )
    date_business_maturity = fields.Date(
        string=u'Business maturity',
    )
    payment_method_id = fields.Many2one(
        comodel_name='account.payment.method',
        string=u'Payment Method',
    )
    payment_term_id = fields.Many2one(
        string=u'Payment term',
        comodel_name='account.payment.term',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account'
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Account',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string=u'Payment Journal',
    )
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string=u'Bank Account',
    )

    def recalculate_balance(self, res):
        balance = 0
        for record in res:
            credit = record['amount_credit']
            debit = record['amount_debit']
            if debit == 0 and credit == 0:
                balance += record['amount_cumulative_balance']
            balance += credit + debit
            record['amount_cumulative_balance'] = balance

    @api.model
    def read_group(self, domain, fields, groupby, offset=0,
                   limit=None, orderby=False, lazy=True):
        res = super(FinancialCashflow, self)\
            .read_group(domain, fields, groupby, offset=offset,
                        limit=limit, orderby=orderby, lazy=lazy)
        self.recalculate_balance(res)
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0,
                    limit=None, order=None):
        res = super(FinancialCashflow, self)\
            .search_read(domain, fields, offset, limit, order=False)
        self.recalculate_balance(res)
        return res

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            DROP VIEW IF EXISTS financial_cashflow;
            DROP VIEW IF EXISTS financial_cashflow_base;
            DROP VIEW IF EXISTS financial_cashflow_debit;
            DROP VIEW IF EXISTS financial_cashflow_bank;
            DROP VIEW IF EXISTS financial_cashflow_credit;
        """)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_credit AS
                SELECT
                    financial_move.create_date,
                    financial_move.id,
                    financial_move.document_number,
                    financial_move.financial_type,

                    financial_move.state,
                    financial_move.date_business_maturity,
                    financial_move.date,
                    financial_move.payment_method_id,
                    financial_move.payment_term_id,

                    financial_move.date_maturity,
                    financial_move.partner_id,
                    financial_move.currency_id,

                    financial_move.account_id,
                    financial_move.analytic_account_id,
                    financial_move.bank_id,
                    financial_move.journal_id,
                    coalesce(financial_move.amount_paid, 0)
                        AS amount_paid,
                    coalesce(financial_move.amount_total, 0)
                        AS amount_total,
                    coalesce(financial_move.amount_residual, 0)
                        AS amount_credit,
                    0 AS amount_debit,
                    coalesce(financial_move.amount_total, 0)
                        AS amount_balance
                FROM
                    public.financial_move
                WHERE
                    financial_move.financial_type = 'r' and
                    financial_move.amount_residual != 0.0
                ;
        """)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_credit_rr AS
                SELECT
                    financial_move.create_date,
                    financial_move.id,
                    financial_move.document_number,
                    financial_move.financial_type,

                    financial_move.state,
                    financial_move.date_business_maturity,
                    financial_move.date,
                    financial_move.payment_method_id,
                    financial_move.payment_term_id,

                    financial_move.date_maturity,
                    financial_move.partner_id,
                    financial_move.currency_id,

                    financial_move.account_id,
                    financial_move.analytic_account_id,
                    financial_move.bank_id,
                    financial_move.journal_id,
                    coalesce(financial_move.amount_paid, 0)
                        AS amount_paid,
                    coalesce(financial_move.amount_total, 0)
                        AS amount_total,
                    coalesce(financial_move.amount_total, 0)
                        AS amount_credit,
                    0 AS amount_debit,
                    coalesce(financial_move.amount_total, 0)
                        AS amount_balance
                FROM
                    public.financial_move
                WHERE
                    financial_move.financial_type = 'rr';
        """)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_bank AS
                SELECT
                    res_partner_bank.date_balance as create_date,
                    res_partner_bank.id * (-1) as id,
                    'Saldo inicial' as  document_number,
                        'open' as financial_type,
                    'residual' as state,
                    res_partner_bank.date_balance as date_business_maturity,
                    res_partner_bank.date_balance as date,
                    res_partner_bank.id as bank_id,
                    NULL as journal_id,
                    NULL as payment_method_id,
                    NULL as payment_term_id,

                    res_partner_bank.date_balance as date_maturity,
                    NULL as partner_id,
                    res_partner_bank.currency_id,
                    NULL as account_id,
                    NULL as analytic_account_id,
                    coalesce(res_partner_bank.initial_balance, 0)
                    as amount_paid,
                    0 as amount_balance,
                    0 as amount_total,
                    coalesce(res_partner_bank.initial_balance, 0)
                        as amount_credit,
                    0 as amount_debit
                FROM public.res_partner_bank
                INNER JOIN public.res_company
                ON res_partner_bank.partner_id = res_company.partner_id;
        """)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_debit AS
                SELECT
                    financial_move.create_date,
                    financial_move.id,
                    financial_move.document_number,
                    financial_move.financial_type,

                    financial_move.state,
                    financial_move.date_business_maturity,
                    financial_move.date,
                    financial_move.payment_method_id,
                    financial_move.payment_term_id,

                    financial_move.date_maturity,
                    financial_move.partner_id,
                    financial_move.currency_id,

                    financial_move.account_id,
                    financial_move.analytic_account_id,
                    financial_move.bank_id,
                    financial_move.journal_id,
                    coalesce(financial_move.amount_paid, 0)
                        AS amount_paid,
                    coalesce(financial_move.amount_total, 0)
                        AS amount_total,
                    0 AS amount_credit,
                    (-1) * coalesce(financial_move.amount_residual, 0)
                        AS amount_debit,
                    (-1) * coalesce(financial_move.amount_total, 0)
                        AS amount_balance
                FROM
                    public.financial_move
                WHERE
                    financial_move.financial_type = 'p' and
                    financial_move.amount_residual != 0.0
                ;
        """)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_debit_pp AS
                SELECT
                    financial_move.create_date,
                    financial_move.id,
                    financial_move.document_number,
                    financial_move.financial_type,

                    financial_move.state,
                    financial_move.date_business_maturity,
                    financial_move.date,
                    financial_move.payment_method_id,
                    financial_move.payment_term_id,

                    financial_move.date_maturity,
                    financial_move.partner_id,
                    financial_move.currency_id,

                    financial_move.account_id,
                    financial_move.analytic_account_id,
                    financial_move.bank_id,
                    financial_move.journal_id,
                    coalesce(financial_move.amount_paid, 0)
                        AS amount_paid,
                    coalesce(financial_move.amount_total, 0)
                        AS amount_total,
                    0 AS amount_credit,
                    (-1) * coalesce(financial_move.amount_total, 0)
                        AS amount_debit,
                    (-1) * coalesce(financial_move.amount_total, 0)
                        AS amount_balance
                FROM
                    public.financial_move
                WHERE
                    financial_move.financial_type = 'pp';
        """)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow_base AS
                SELECT
                    c.create_date,
                    c.id,
                    c.document_number,
                    c.financial_type,
                    c.state,
                    c.date_business_maturity,
                    c.date,
                    c.payment_method_id,
                    c.payment_term_id,
                    c.date_maturity,
                    c.partner_id,
                    c.currency_id,
                    c.account_id,
                    c.analytic_account_id,
                    c.journal_id,
                    c.bank_id,
                    c.amount_total,
                    c.amount_paid,
                    c.amount_credit,
                    c.amount_debit,
                    c.amount_balance
                FROM
                    financial_cashflow_credit c

                UNION ALL

                SELECT
                    crr.create_date,
                    crr.id,
                    crr.document_number,
                    crr.financial_type,
                    crr.state,
                    crr.date_business_maturity,
                    crr.date,
                    crr.payment_method_id,
                    crr.payment_term_id,
                    crr.date_maturity,
                    crr.partner_id,
                    crr.currency_id,
                    crr.account_id,
                    crr.analytic_account_id,
                    crr.journal_id,
                    crr.bank_id,
                    crr.amount_total,
                    crr.amount_paid,
                    crr.amount_credit,
                    crr.amount_debit,
                    crr.amount_balance
                FROM
                    financial_cashflow_credit_rr crr

                UNION ALL

                SELECT
                    d.create_date,
                    d.id,
                    d.document_number,
                    d.financial_type,
                    d.state,
                    d.date_business_maturity,
                    d.date,
                    d.payment_method_id,
                    d.payment_term_id,
                    d.date_maturity,
                    d.partner_id,
                    d.currency_id,
                    d.account_id,
                    d.analytic_account_id,
                    d.journal_id,
                    d.bank_id,
                    d.amount_total,
                    d.amount_paid,
                    d.amount_credit,
                    d.amount_debit,
                    d.amount_balance
                FROM
                    financial_cashflow_debit d

                UNION ALL
                SELECT
                    dpp.create_date,
                    dpp.id,
                    dpp.document_number,
                    dpp.financial_type,
                    dpp.state,
                    dpp.date_business_maturity,
                    dpp.date,
                    dpp.payment_method_id,
                    dpp.payment_term_id,
                    dpp.date_maturity,
                    dpp.partner_id,
                    dpp.currency_id,
                    dpp.account_id,
                    dpp.analytic_account_id,
                    dpp.journal_id,
                    dpp.bank_id,
                    dpp.amount_total,
                    dpp.amount_paid,
                    dpp.amount_credit,
                    dpp.amount_debit,
                    dpp.amount_balance
                FROM
                    financial_cashflow_debit_pp dpp

                UNION ALL

                SELECT
                    b.create_date,
                    b.id,
                    b.document_number,
                    b.financial_type,
                    b.state,
                    b.date_business_maturity,
                    b.date,
                    b.payment_method_id,
                    b.payment_term_id,
                    b.date_maturity,
                    b.partner_id,
                    b.currency_id,
                    b.account_id,
                    b.analytic_account_id,
                    b.journal_id,
                    b.bank_id,
                    b.amount_total,
                    b.amount_paid,
                    b.amount_credit,
                    b.amount_debit,
                    b.amount_balance
                FROM
                    financial_cashflow_bank b
        """)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cashflow AS
                SELECT
                    b.create_date,
                    b.id,
                    b.document_number,
                    b.financial_type,
                    b.state,
                    b.date_business_maturity,
                    b.date,
                    b.payment_method_id,
                    b.payment_term_id,
                    b.date_maturity,
                    b.partner_id,
                    b.currency_id,
                    b.account_id,
                    b.analytic_account_id,
                    b.journal_id,
                    b.bank_id,
                    b.amount_total,
                    b.amount_paid,
                    b.amount_credit,
                    b.amount_debit,
                    b.amount_balance,
                    SUM(b.amount_balance)
                    OVER (order by b.date_business_maturity, b.id)
                        AS amount_cumulative_balance
                    -- aqui deveria haver um campo balance_date ou algo assim
                    -- que seria a data de crédito/débito efetivo na conta
                    -- pois boletos e cheques tem data de crédito d+1 ou d+2
                    -- após o depósito/pagamento. Exemplo:
                    -- over(order by b.data_credito_debito)
                FROM
                    financial_cashflow_base b;
        """)

    @api.model
    def _query_get(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(str(domain)) or []

        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            if not context.get('strict_range'):
                domain += ['|', (date_field, '>=', context['date_from']), (
                    'account_id.user_type_id.include_initial_balance', '=',
                    True)]
            elif context.get('initial_bal'):
                domain += [(date_field, '<', context['date_from'])]
            else:
                domain += [(date_field, '>=', context['date_from'])]

        # if context.get('journal_ids'):
        #     domain += [('journal_id', 'in', context['journal_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]

        # if context.get('reconcile_date'):
        #     domain += ['|', ('reconciled', '=', False), '|', (
        #         'matched_debit_ids.create_date', '>',
        #         context['reconcile_date']), (
        #         'matched_credit_ids.create_date', '>',
        #         context['reconcile_date'])]

        if context.get('account_tag_ids'):
            domain += [
                ('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

        if context.get('analytic_tag_ids'):
            domain += ['|', (
                'analytic_account_id.tag_ids', 'in',
                context['analytic_tag_ids'].ids),
                ('analytic_tag_ids', 'in',
                    context['analytic_tag_ids'].ids)]

        if context.get('analytic_account_ids'):
            domain += [
                ('analytic_account_id', 'in',
                 context['analytic_account_ids'].ids)]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            query = self._where_calc(domain)
            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params
