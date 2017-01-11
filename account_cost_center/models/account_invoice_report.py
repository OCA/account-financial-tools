# -*- coding: utf-8 -*-
# Copyright 2015-2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    cost_center_id = fields.Many2one(
        'account.cost.center',
        string='Cost Center',
        readonly=True
    )
    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        readonly=True
    )

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + \
            ", sub.cost_center_id as cost_center_id, " + \
            "sub.account_analytic_id as account_analytic_id"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + \
            ", ail.cost_center_id as cost_center_id, " + \
            "ail.account_analytic_id as account_analytic_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + \
            ", ail.cost_center_id, " + \
            "ail.account_analytic_id"
