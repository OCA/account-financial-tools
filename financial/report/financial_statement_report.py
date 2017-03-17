# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FinancialStatementReport(models.Model):

    _name = 'financial.statement.report'
    _description = 'Financial Statement Report'
    _inherit = 'accounting.report'

    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account'
    )
