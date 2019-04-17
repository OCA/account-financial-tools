# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from datetime import datetime
from openerp import fields, models, api

from ..constants import (
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_DEBT_2PAY
)

STATEMENT_TYPE = [
    (FINANCIAL_DEBT_2RECEIVE, 'Client'),
    (FINANCIAL_DEBT_2PAY, 'Supplier')
]


class ReportXlsxFinancialFinancialPartnerStatementWizard(
        models.TransientModel):
    _name = 'report.xlsx.financial.partner.statement.wizard'
    _description = 'Report Xlsx Financial Partner Statement Wizard'

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == '2pay':
            field = 'supplier'
        else:
            field = 'customer'
        domain = {'domain': {'partner_id': [(field, '=', True)]}}
        return domain

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
    )
    date_from = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-%m-01'),
    )
    date_to = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-12-31'),
    )
    type = fields.Selection(
        string='Statement type',
        selection=STATEMENT_TYPE,
        required=True,  # FIXME this field can be blank if sql is improoved
    )

    @api.multi
    def generate_report(self):
        self.ensure_one()
        return self.env.ref(
            'financial.report_xlsx_financial_partner_statement_action'
        ).report_action(self)

