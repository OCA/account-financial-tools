# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Aristides Caldeira <aristides.caldeira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from .report_xlsx_financial_base import ReportXlsxFinancialBase
from odoo.report import report_sxw
from odoo import _
from odoo import fields
from dateutil.relativedelta import relativedelta


class ReportXslxFinancialCashflow(ReportXlsxFinancialBase):

    def define_title(self):
        if self.report_wizard.time_span == 'days':
            if self.report_wizard.period == 'date_maturity':
                title = _('Expected Dayly Cashflow')
            else:
                title = _('Realized Dayly Cashflow')
        elif self.report_wizard.time_span == 'weeks':
            if self.report_wizard.period == 'date_maturity':
                title = _('Expected Weekly Cashflow')
            else:
                title = _('Realized Weekly Cashflow')
        else:
            if self.report_wizard.period == 'date_maturity':
                title = _('Expected Monthly Cashflow')
            else:
                title = _('Realized Monthly Cashflow')

        return title

    def define_filters(self):
        date_from = fields.Datetime.from_string(self.report_wizard.date_from)
        date_from = date_from.date()
        date_to = fields.Datetime.from_string(self.report_wizard.date_to)
        date_to = date_to.date()

        filters = {
            0: {
                'title': _('Date'),
                'value': _('From %s to %s') %
                (date_from.strftime('%d/%m/%Y'),
                 date_to.strftime('%d/%m/%Y')),
            },
            1: {
                'title': _('Company'),
                'value': self.report_wizard.company_id.name,
            },

        }
        return filters

    def define_filter_title_column_span(self):
        return 2

    def define_filter_value_column_span(self):
        return 3

    def prepare_data(self):
        #
        # First, we prepare the report_data lines, time_span and accounts
        #
        report_data = {
            'time_span_titles': {},
            'lines': {},
            'summaries': {},
            'summaries_total': {},
            'summaries_accumulated': {},
        }

        date_from = fields.Datetime.from_string(self.report_wizard.date_from)
        date_from = date_from.date()
        date_to = fields.Datetime.from_string(self.report_wizard.date_to)
        date_to = date_to.date()

        if self.report_wizard.time_span == 'days':
            current_date = date_from
            while current_date <= date_to:
                title = current_date.strftime('%d/%m/%Y')
                time_span_date = 'value_' + str(current_date).replace('-', '_')
                report_data['time_span_titles'][time_span_date] = title
                current_date += relativedelta(days=1)

        elif self.report_wizard.time_span == 'weeks':
            current_date = date_from
            while current_date <= date_to:
                title = current_date.strftime('%V/%Y')
                time_span_date = 'value_' + str(current_date).replace('-', '_')
                report_data['time_span_titles'][time_span_date] = title
                current_date += relativedelta(weeks=1)
        else:
            current_date = date_from + relativedelta(day=1)
            last_date = date_to + relativedelta(day=1)
            while current_date <= last_date:
                title = current_date.strftime('%B/%Y')
                time_span_date = 'value_' + str(current_date).replace('-', '_')
                report_data['time_span_titles'][time_span_date] = title
                current_date += relativedelta(months=1)

        accounts = self.env['financial.account'].search([], order='code')
        for account in accounts:
            line = {
                'account_code': account.code,
                'account_name': account.name,
                'initial_value': 0,
                'final_value': 0,
            }

            for time_span_date in report_data['time_span_titles'].keys():
                line[time_span_date] = 0

            report_data['lines'][account.code] = line

            if account.level == 1:
                report_data['summaries'][account.code] = line

        #
        # Now the summaries_total and summaries_accumulated lines
        #
        line = {
            'account_code': '',
            'account_name': 'TOTAL',
            'initial_value': 0,
            'final_value': 0,
        }

        for time_span_date in report_data['time_span_titles'].keys():
            line[time_span_date] = 0

        report_data['summaries_total'] = line

        line = {
            'account_code': '',
            'account_name': 'ACCUMULATED TOTAL',
            'initial_value': 0,
            'final_value': 0,
        }

        for time_span_date in report_data['time_span_titles'].keys():
            line[time_span_date] = 0

        report_data['summaries_accumulated'] = line

        #
        # Now, the actual report data
        #
        sql_filter = {
            'period': self.report_wizard.period,
            'date_from': self.report_wizard.date_from,
            'date_to': self.report_wizard.date_to,
        }

        if self.report_wizard.period == 'date_maturity':
            sql_filter['type'] = 'in'

            if self.report_wizard.time_span == 'days':
                sql_filter['time_span'] = 'fm.date_maturity'
            elif self.report_wizard.time_span == 'weeks':
                sql_filter['time_span'] = "to_char(fm.date_maturity, 'IYYY')"
            else:
                sql_filter[
                    'time_span'] = "to_char(fm.date_maturity, 'YYYY-MM-01')"

        else:
            sql_filter['type'] = 'not in'

            if self.report_wizard.time_span == 'days':
                sql_filter[
                    'time_span'] = 'coalesce(fm.date_credit_debit, fm.date_payment)'
            elif self.report_wizard.time_span == 'weeks':
                sql_filter[
                    'time_span'] = "to_char(coalesce(fm.date_credit_debit, fm.date_payment), 'IYYY')"
            else:
                sql_filter[
                    'time_span'] = "to_char(coalesce(fm.date_credit_debit, fm.date_payment), 'YYYY-MM-01')"

        SQL_INICIAL_VALUE = '''
            select
                fa.code,
                sum(fm.amount_total * fm.sign)
            from
                financial_move fm
                join financial_account_tree_analysis fat on fat.child_account_id = fm.account_id
                join financial_account fa on fa.id = fat.parent_account_id
            where
                fm.type {type} ('2receive', '2pay')
                and fm.{period} < '{date_from}'
                
            group by
                fa.code
                
            order by
                fa.code
        '''
        sql = SQL_INICIAL_VALUE.format(**sql_filter)
        self.env.cr.execute(sql)
        data = self.env.cr.fetchall()

        for account_code, value in data:
            if account_code in report_data['lines']:
                report_data['lines'][account_code][
                    'initial_value'] = value or 0
                report_data['lines'][account_code]['final_value'] = value or 0

            if account_code in report_data['summaries']:
                # report_data['summaries'][account_code]['initial_value'] += \
                #     value or 0
                # report_data['summaries'][account_code]['final_value'] += \
                #     value or 0
                report_data['summaries_total']['initial_value'] += value or 0
                report_data['summaries_total']['final_value'] += value or 0

        SQL_DATA = '''
            select
                fa.code,
                {time_span} as time_span_date,
                sum(fm.amount_total * fm.sign)
            from
                financial_move fm
                join financial_account_tree_analysis fat on fat.child_account_id = fm.account_id
                join financial_account fa on fa.id = fat.parent_account_id
            where
                fm.type {type} ('2receive', '2pay')
                and fm.{period} between '{date_from}' and '{date_to}'
                
            group by
                fa.id, fa.code, time_span_date
                
            order by
                fa.code, time_span_date
        '''
        sql = SQL_DATA.format(**sql_filter)
        print(sql)
        self.env.cr.execute(sql)
        data = self.env.cr.fetchall()

        for account_code, time_span_date, value in data:
            time_span_date = 'value_' + time_span_date.replace('-', '_')
            if account_code not in report_data['lines']:
                # raise ?
                continue

            if time_span_date not in report_data['lines'][account_code]:
                # raise ?
                continue

            report_data['lines'][account_code][time_span_date] = \
                value or 0
            report_data['lines'][account_code]['final_value'] += value or 0

            if account_code in report_data['summaries']:
                report_data['summaries_total'][time_span_date] += \
                    value or 0
                report_data['summaries_total']['final_value'] += \
                    value or 0

        return report_data

    def define_columns(self):
        result = {
            0: {
                'header': _('Conta'),
                'field': 'account_code',
                'width': 12,
            },
            1: {
                'header': _('Name'),
                'field': 'account_name',
                'width': 25,
            },
            2: {
                'header': _('Initial'),
                'field': 'initial_value',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
        }

        time_span_titles = self.report_data['time_span_titles']

        next_col = 3
        for time_span_date in sorted(time_span_titles.keys()):
            result[next_col] = {
                'header': time_span_titles[time_span_date],
                'field': time_span_date,
                'style': 'currency',
                'width': 20,
                'type': 'currency',
            }
            next_col += 1

        result[next_col] = {
            'header': _('Final'),
            'field': 'final_value',
            'style': 'currency',
            'width': 20,
            'type': 'formula',
            'formula':
                '=SUM(C{current_row}:{previous_column}{current_row})',
        }

        return result

    def define_columns_summary_total(self):
        result = {
            0: {
                'header': _('Conta'),
                'field': 'account_code',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': _('Name'),
                'field': 'account_name',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': _('Initial'),
                'field': 'initial_value',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '=SUM({current_column}{first_row}:{current_column}{previous_row})',
            },
        }

        time_span_titles = self.report_data['time_span_titles']

        next_col = 3
        for time_span_date in sorted(time_span_titles.keys()):
            result[next_col] = {
                'header': time_span_titles[time_span_date],
                'field': time_span_date,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '=SUM({current_column}{first_row}:{current_column}{previous_row})',
            }
            next_col += 1

        result[next_col] = {
            'header': _('Final'),
            'field': 'final_value',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '=SUM(C{current_row}:{previous_column}{current_row})',
        }

        return result

    def define_columns_summary_accumulated(self):
        result = {
            0: {
                'header': _('Conta'),
                'field': 'account_code',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': _('Name'),
                'field': 'account_name',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': _('Initial'),
                'field': 'initial_value',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '={current_column}{previous_row}',
            },
        }

        time_span_titles = self.report_data['time_span_titles']

        next_col = 3
        for time_span_date in sorted(time_span_titles.keys()):
            result[next_col] = {
                'header': time_span_titles[time_span_date],
                'field': time_span_date,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '={previous_column}{current_row} + {current_column}{previous_row}',
            }
            next_col += 1

        result[next_col] = {
            'header': _('Final'),
            'field': 'final_value',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '={previous_column}{current_row}',
        }

        return result

    def define_columns_detail_total(self):
        result = {
            0: {
                'header': _('Conta'),
                'field': 'account_code',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': _('Name'),
                'field': 'account_name',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': _('Initial'),
                'field': 'initial_value',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '={current_column}{summary_total_row}',
            },
        }

        time_span_titles = self.report_data['time_span_titles']

        next_col = 3
        for time_span_date in sorted(time_span_titles.keys()):
            result[next_col] = {
                'header': time_span_titles[time_span_date],
                'field': time_span_date,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '={current_column}{summary_total_row}',
            }
            next_col += 1

        result[next_col] = {
            'header': _('Final'),
            'field': 'final_value',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '={current_column}{summary_total_row}',
        }

        return result

    def define_columns_detail_accumulated(self):
        result = {
            0: {
                'header': _('Conta'),
                'field': 'account_code',
                'width': 12,
                'style': self.style.header.align_left,
            },
            1: {
                'header': _('Name'),
                'field': 'account_name',
                'width': 25,
                'style': self.style.header.align_left,
            },
            2: {
                'header': _('Initial'),
                'field': 'initial_value',
                'width': 20,
                'style': self.style.header.currency,
                'type': 'formula',
                'formula':
                    '={current_column}{summary_accumulated_row}',
            },
        }

        time_span_titles = self.report_data['time_span_titles']

        next_col = 3
        for time_span_date in sorted(time_span_titles.keys()):
            result[next_col] = {
                'header': time_span_titles[time_span_date],
                'field': time_span_date,
                'style': self.style.header.currency,
                'width': 20,
                'type': 'formula',
                'formula':
                '={current_column}{summary_accumulated_row}',
            }
            next_col += 1

        result[next_col] = {
            'header': _('Final'),
            'field': 'final_value',
            'style': self.style.header.currency,
            'width': 20,
            'type': 'formula',
            'formula':
                '={current_column}{summary_accumulated_row}',
        }

        return result

    def write_content(self):
        self.sheet.set_zoom(85)

        #
        # Summary
        #
        total_columns = self.define_columns_summary_total()
        accumulated_columns = self.define_columns_summary_accumulated()

        self.sheet.merge_range(
            self.current_row, 0, self.current_row + 1, len(self.columns) - 1,
            _('Summmary'), self.style.header.align_center
        )
        self.current_row += 2
        self.write_header()

        first_data_row = self.current_row + 1
        for account_code in sorted(self.report_data['summaries'].keys()):
            self.write_detail(self.report_data['summaries'][account_code])

        self.write_detail(self.report_data['summaries_total'], total_columns,
                          first_data_row)
        summary_total_row = self.current_row
        self.write_detail(self.report_data['summaries_accumulated'],
                          accumulated_columns)
        summary_accumulated_row = self.current_row

        #
        # Detail
        #
        total_columns = self.define_columns_detail_total()
        accumulated_columns = self.define_columns_detail_accumulated()
        formula_changes = {
            'summary_total_row': summary_total_row,
            'summary_accumulated_row': summary_accumulated_row,
        }

        self.current_row += 1
        self.sheet.merge_range(
            self.current_row, 0, self.current_row + 1, len(self.columns) - 1,
            _('Detail'), self.style.header.align_center
        )
        self.current_row += 2
        self.write_header()

        first_data_row = self.current_row
        for account_code in sorted(self.report_data['lines'].keys()):
            self.write_detail(self.report_data['lines'][account_code])

        self.write_detail(self.report_data['summaries_total'], total_columns,
                          first_data_row, formula_changes=formula_changes)
        self.write_detail(self.report_data['summaries_accumulated'],
                          accumulated_columns, formula_changes=formula_changes)

    def generate_xlsx_report(self, workbook, data, report_wizard):
        super(ReportXslxFinancialCashflow, self).generate_xlsx_report(
            workbook, data, report_wizard)

        workbook.set_properties({
            'title': self.title,
            'company': self.report_wizard.company_id.name,
            'comments': _('Created with Financial app on {now}').format(
                now=fields.Datetime.now())
        })

        #
        # Documentation for formatting pages here:
        # http://xlsxwriter.readthedocs.io/page_setup.html
        #
        self.sheet.set_landscape()
        self.sheet.set_paper(9)  # A4
        self.sheet.fit_to_pages(1, 99999)
        #
        # Margins, in inches, left, right, top, bottom;
        # 1 / 2.54 = 1 cm converted in inches
        #
        self.sheet.set_margins(1 / 2.54, 1 / 2.54, 1 / 2.54, 1 / 2.54)


ReportXslxFinancialCashflow(
    #
    # Name of the report in report_xlsx_financial_cashflow_data.xml,
    # field name, *always* preceeded by "report."
    #
    'report.report_xlsx_financial_cashflow',
    #
    # The model used to filter report data, or where the data come from
    #
    'report.xlsx.financial.cashflow.wizard',
    parser=report_sxw.rml_parse
)
