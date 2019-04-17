# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from datetime import datetime
from openerp import fields, models, api, _


class ReportXlsxFinancialFinancialMovesStatesWizard(models.TransientModel):
    _name = 'report.xlsx.financial.moves.states.wizard'
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
            ('date_business_maturity', _('Maturity')),
            ('partner_id', _('Partner')),
        ],
        default='date_business_maturity',
    )
    selected_partners = fields.Many2many(
        comodel_name="res.partner",
        relation="financial_move_partner",
        column1="wizard_id",
        column2="partner_id",
    )
    type = fields.Selection(
        string=_('Type'),
        required=True,
        selection=[
            ('2receive', _('To Receive')),
            ('2pay', _('To Pay'))
        ],
        default='2receive',
    )
    move_state = fields.Selection(
        string=_('State'),
        selection=[
            ('open', 'Open'),
            ('paid', 'Paid'),
        ],
        help=_(
            "If none of the options was selected, all of them will be search!"
        )
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

        return self.env['report'].get_action(
            self,
            report_name='report_xlsx_financial_moves_states'
        )
