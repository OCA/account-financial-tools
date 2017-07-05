# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from . import abstract_test_report


class TestCashFlow(abstract_test_report.AbstractTestReport):
    """
        Technical tests for Cash Flow Report.
    """

    def _getReportModel(self):
        return self.env['report.xlsx.financial.cashflow.wizard']

    def _getXlsxReportName(self):
        return 'report_xlsx_financial_cashflow'

    def _getXlsxReportActionName(self):
        return 'financial.report_xlsx_financial_cashflow_action'

    def _getReportTitle(self):
        return 'Cash Flow'

    def _getBaseFilters(self):
        return {
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': self.env.ref('base.main_company').id,
            'time_span': 'days',
            'period': 'date_maturity',
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'time_span': 'weeks', 'period': 'date_maturity'},
            # {'time_span': 'months', 'period': 'date_maturity'},
            {'time_span': 'days', 'period': 'date_credit_debit'},
            {'time_span': 'weeks', 'period': 'date_credit_debit'},
            # {'time_span': 'months', 'period': 'date_credit_debit'},
        ]

    def _partner_test_is_possible(self, filters):
        # return 'show_partner_details' in filters
        return False
