# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from odoo import api, fields, models


class FinancialStatementReport(models.Model):
    _name = 'financial.statement.report'
    _inherit = 'accounting.report'
    _transient = False

    name = fields.Char(
        string=u'Name',
        required=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account'
    )
    date_report = fields.Datetime(
        string=u"Date report",
        readonly=True,
    )
    report_format = fields.Selection(
        string=u"Report format",
        selection=[
            ('pdf', u'PDF'),
            ('xls', u'XLS'), # TODO
        ]
    )
    included_ids = fields.One2many(
        comodel_name='financial.statement.report.included',
        inverse_name='financial_statement_report_id',
        string=u"Included accounts"
    )
    not_included_ids = fields.One2many(
        comodel_name='financial.statement.report.not_included',
        inverse_name='financial_statement_report_id',
        string=u"Included accounts"
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id',
    )

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search(
            [('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(
            data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(
                data.get('comparison_context'))._compute_report_balance(
                child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get(
                            'account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * report.sign,
                'type': 'report',
                'level': bool(
                    report.style_overwrite
                ) and report.style_overwrite or report.level,
                'account_type': report.type or False,
                # used to underline the financial report balances
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # the rest of the loop is used to display the details of the
                # financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    # if there are accounts to display, we add them to the
                    # lines with a level equals to their level in
                    # the COA + 1 (to avoid having them with a too low level
                    #  that would conflicts with the level of data
                    # financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'level': (
                            report.display_detail ==
                            'detail_with_hierarchy' and 4),
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if (not account.company_id.currency_id.is_zero(
                            vals['debit']) or not
                                account.company_id.currency_id.is_zero(
                                vals['credit'])):
                            flag = True
                    if not account.company_id.currency_id.is_zero(
                            vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(
                                vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines,
                                key=lambda sub_line: sub_line['name'])
        return lines

    def _compute_report_balance(self, reports):
        """ Returns a dictionary with key=the ID of a record and value=the
        credit, debit and balance amount computed for this record.
        If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with
           such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a
           'view' record)
        """
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(
                    report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search(
                    [('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(
                    accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def _compute_account_balance(self, accounts):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance':
                """COALESCE(
                SUM(amount_debit),0) - COALESCE(
                SUM(amount_credit), 0) as balance""",
            'debit': "COALESCE(SUM(amount_debit), 0) as debit",
            'credit': "COALESCE(SUM(amount_credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = self.env[
                'financial.cashflow']._query_get()
            tables = tables.replace('"', '') if \
                tables else "financial_cashflow"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(
                mapping.values()) + \
                " FROM " + tables + \
                " WHERE account_id IN %s " \
                + filters + \
                " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            print request, '    ', params
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    @api.multi
    def action_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.ids
        data['model'] = self._name
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids',
                                  'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context,
            lang=self.env.context.get('lang', 'en_US')
        )
        data['form'].update(self.read(
            ['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp',
             'account_report_id', 'enable_filter', 'label_filter',
             'target_move'])[0])
        res = self.env['report'].get_action(self, 'account.report_financial',
                                            data)
        data = {}
        data['form'] = self.read(
            ['account_report_id', 'date_from_cmp', 'date_to_cmp',
             'journal_ids', 'filter_cmp', 'target_move'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        res['data']['form']['comparison_context'] = comparison_context

        self.included_ids.unlink()
        for line in self.get_account_lines(res['data']['form']):
            line['financial_statement_report_id'] = self.id
            self.included_ids.create(line)
        self.date_report = fields.Datetime.now()
        return self.env['report'].get_action(
            self, 'financial.report_financial_statement')


class ReportFinancialStatement(models.AbstractModel):
    _name = 'report.financial.report_financial_statement'

    @api.model
    def render_html(self, docids, data=None):
        docs = self.env['financial.statement.report'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'financial.statement.report',
            'data': docs.read([])[0],
            'docs': docs,
            'time': time,
            'get_account_lines': docs.included_ids.read(
                ['account_type', 'balance', 'type', 'name', 'level']
            ),
        }
        return self.env['report'].render(
            'financial.report_financial_statement', docargs)


class FinancialStatementReportIncluded(models.Model):
    _name = 'financial.statement.report.included'

    name = fields.Char(
        string=u"Name",
    )
    type = fields.Char(

    )
    account_type = fields.Char(

    )
    level = fields.Integer(
        string="Level"
    )
    # currency_id = fields.Many2one(
    #     related='financial_statement_report_id.currency_id',
    # )
    balance = fields.Float(
        string=u"Amount",
        default=0.00,
    )
    financial_statement_report_id = fields.Many2one(
        comodel_name='financial.statement.report',
    )


class FinancialStatementReportNotIncluded(models.Model):
    _name = 'financial.statement.report.not_included'

    name = fields.Char(
        string=u"Code",
        related='account_id.code',
    )
    account_id = fields.Many2one(
        string=u"Account",
        comodel_name='account.account',
    )
    currency_id = fields.Many2one(
        related='financial_statement_report_id.currency_id',
    )
    amount = fields.Monetary(
        string=u"Amount",
        default=0.00,
    )
    financial_statement_report_id = fields.Many2one(
        comodel_name='financial.statement.report',
    )
