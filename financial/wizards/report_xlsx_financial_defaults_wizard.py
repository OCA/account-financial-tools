# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from datetime import datetime
from openerp import fields, models, api, _


class ReportXlsxFinancialDefaultsWizard(models.TransientModel):
    _name = 'report.xlsx.financial.defaults.wizard'
    _description = 'Report Xlsx Financial Defaults Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    selected_partners = fields.Many2many(
        comodel_name="res.partner",
        relation="financial_move_partner_defaults",
        column1="wizard_id",
        column2="partner_id",
        required=True,
    )
    date_from = fields.Date(
        string=_("Date From"),
        required=True,
        default=datetime.now().strftime('%Y-%m-01'),
    )
    date_to = fields.Date(
        string=_("Date To"),
        required=True,
        default=datetime.now().strftime('%Y-12-31'),
    )

    @api.multi
    def generate_report(self):
        self.ensure_one()
        return self.env.ref(
            'financial.report_xlsx_financial_defaults'
        ).report_action(self)
