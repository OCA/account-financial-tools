# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
import datetime


class FinancialPayreceive(models.TransientModel):

    _name = 'wizard.financial.cashflow'

    period = fields.Selection(
        string='Period',
        required=False,
        selection=[
            ('periodo_previsto', u'Periodo Previsto'),
            ('periodo_realizado', u'Periodo Realizado')
        ],
    )

    date_from = fields.Date(
        string='Date From',
    )
    date_to = fields.Date(
        string='Date To',
    )


    @api.multi
    def doit(self):
        """
        Método disparado pela view
        :return:
        """
        return True
