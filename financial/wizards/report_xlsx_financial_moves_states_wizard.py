# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from datetime import datetime
from openerp import fields, models, api


class ReportXlsxFinancialFinancialMovesStatesWizard(models.TransientModel):
    _name = b'report.xlsx.financial.moves.states.wizard'
    _description = 'Report Xlsx Financial Moves States Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    group_by = fields.Selection(
        string='Group By',
        required=True,
        selection=[
            ('date_business_maturity', 'Maturity'),
            ('partner_id', 'Partner'),
        ],
        default='date_business_maturity',
    )
    type = fields.Selection(
        string='Type',
        required=True,
        selection=[
            ('2receive', 'To Receive'),
            ('2pay', 'To Pay')
        ],
        default='2receive',
    )
    date_from = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-%m-01'),
    )
    date_to = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-12-31'),
    )

    @api.multi
    def generate_report(self):
        self.ensure_one()

        return self.env['report'].get_action(
            self,
            report_name='report_xlsx_financial_moves_states'
        )
