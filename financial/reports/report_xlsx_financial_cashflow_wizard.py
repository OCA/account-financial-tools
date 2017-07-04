# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Aristides Caldeira <aristides.caldeira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from datetime import datetime
from odoo import api, fields, models


class ReportXlsxFinancialCashflowWizard(models.TransientModel):
    _name = b'report.xlsx.financial.cashflow.wizard'
    _description = 'Report Xlsx Financial Cashflow Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    time_span = fields.Selection(
        string='By time span in',
        required=True,
        default='months',
        selection=[
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
        ],
    )
    period = fields.Selection(
        string='Period',
        required=True,
        default='date_maturity',
        selection=[
            ('date_maturity', 'Período Previsto'),
            ('date_credit_debit', 'Período Realizado')
        ],
    )
    date_from = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-%m-01'),
    )
    date_to = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-12-31'),
    )

    def generate_report(self):
        self.ensure_one()
        return self.env['report'].get_action(
            docids=self.ids,
            report_name='report_xlsx_financial_cashflow'
        )
