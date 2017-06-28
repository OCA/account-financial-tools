# -*- coding: utf-8 -*-
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class FinancialCashflowReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * TrialBalanceReport
    ** TrialBalanceReportAccount
    *** TrialBalanceReportPartner
            If "show_partner_details" is selected
    """

    _name = 'report_financial_cashflow'

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()

    only_posted_moves = fields.Boolean()
    hide_account_balance_at_0 = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')


class FinancialCashflowReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_financial_cashflow'

    @api.multi
    def print_report(self, xlsx_report=False):
        self.ensure_one()
        # self.compute_data_for_report()
        if xlsx_report:
            report_name = 'financial.report_financial_cashflow_xlsx'

        return self.env['report'].get_action(
            docids=self.ids, report_name=report_name)
