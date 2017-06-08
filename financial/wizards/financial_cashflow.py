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
            ('date_maturity', u'Periodo Previsto'),
            ('date_payment', u'Periodo Realizado')
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
        SQL = '''
            SELECT
                aa.code, aa.name, fm.{}, SUM(fm.amount_total * fm.sign)
            FROM
                financial_move fm
            JOIN
                account_account_tree_analysis aat
                ON aat.child_account_id = fm.account_id
            JOIN
                account_account aa on aa.id = aat.parent_account_id
            WHERE
                fm.type not in ('2receive', '2pay')
                AND {} <= '{}' AND {} <= '{}'
            GROUP BY
                aa.code, aa.name, fm.{}
        '''

        SQL = SQL.format(self.period, self.period, self.date_from,
                         self.period, self.date_to, self.period)

        result = self._cr.execute(SQL)

        return True
