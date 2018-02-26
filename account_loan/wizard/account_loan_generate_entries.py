# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime


class AccountLoanGenerateWizard(models.TransientModel):
    _name = "account.loan.generate.wizard"

    date = fields.Date(
        'Account Date',
        required=True,
        help="Choose the period for which you want to automatically post the "
             "depreciation lines of running assets",
        default=fields.Date.context_today)
    loan_type = fields.Selection([
        ('leasing', 'Leasings'),
        ('loan', 'Loans'),
    ], required=True, default='loan')

    def run_leasing(self):
        created_ids = self.env['account.loan'].generate_leasing_entries(
            datetime.strptime(self.date, DF).date())
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        if len(created_ids) == 0:
            return
        result['domain'] = [
            ('id', 'in', created_ids),
            ('type', '=', 'in_invoice')
        ]
        return result

    def run_loan(self):
        created_ids = self.env['account.loan'].generate_loan_entries(
            datetime.strptime(self.date, DF).date())
        action = self.env.ref('account.action_move_line_form')
        result = action.read()[0]
        if len(created_ids) == 0:
            return
        result['domain'] = [('id', 'in', created_ids)]
        return result

    @api.multi
    def run(self):
        self.ensure_one()
        if self.loan_type == 'leasing':
            return self.run_leasing()
        return self.run_loan()
