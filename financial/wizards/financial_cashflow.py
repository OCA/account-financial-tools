# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from __future__ import division, print_function, unicode_literals

from operator import itemgetter
from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists

MONTH = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro',
}

SQL_ACCOUNT_TREE_ANALYSIS_VIEW = '''
create or replace view account_account_tree_analysis_view as
select
    a1.id as parent_account_id,
    a1.id as child_account_id,
    1 as level
from
    account_account a1

union all

select
    a2.id as parent_account_id,
    a1.id as child_account_id,
    2 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id

union all

select
    a3.id as parent_account_id,
    a1.id as child_account_id,
    3 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id

union all

select
    a4.id as parent_account_id,
    a1.id as child_account_id,
    4 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id
    join account_account a4 on a3.parent_id = a4.id

union all

select
    a5.id as parent_account_id,
    a1.id as child_account_id,
    5 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id
    join account_account a4 on a3.parent_id = a4.id
    join account_account a5 on a4.parent_id = a5.id

union all

select
    a6.id as parent_account_id,
    a1.id as child_account_id,
    6 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id
    join account_account a4 on a3.parent_id = a4.id
    join account_account a5 on a4.parent_id = a5.id
    join account_account a6 on a5.parent_id = a6.id

union all

select
    a7.id as parent_account_id,
    a1.id as child_account_id,
    7 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id
    join account_account a4 on a3.parent_id = a4.id
    join account_account a5 on a4.parent_id = a5.id
    join account_account a6 on a5.parent_id = a6.id
    join account_account a7 on a6.parent_id = a7.id

union all

select
    a8.id as parent_account_id,
    a1.id as child_account_id,
    8 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id
    join account_account a4 on a3.parent_id = a4.id
    join account_account a5 on a4.parent_id = a5.id
    join account_account a6 on a5.parent_id = a6.id
    join account_account a7 on a6.parent_id = a7.id
    join account_account a8 on a7.parent_id = a8.id

union all

select
    a9.id as parent_account_id,
    a1.id as child_account_id,
    9 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id
    join account_account a4 on a3.parent_id = a4.id
    join account_account a5 on a4.parent_id = a5.id
    join account_account a6 on a5.parent_id = a6.id
    join account_account a7 on a6.parent_id = a7.id
    join account_account a8 on a7.parent_id = a8.id
    join account_account a9 on a8.parent_id = a9.id

union all

select
    a10.id as parent_account_id,
    a1.id as child_account_id,
    10 as level
from
    account_account a1
    join account_account a2 on a1.parent_id = a2.id
    join account_account a3 on a2.parent_id = a3.id
    join account_account a4 on a3.parent_id = a4.id
    join account_account a5 on a4.parent_id = a5.id
    join account_account a6 on a5.parent_id = a6.id
    join account_account a7 on a6.parent_id = a7.id
    join account_account a8 on a7.parent_id = a8.id
    join account_account a9 on a8.parent_id = a9.id
    join account_account a10 on a9.parent_id = a10.id;
'''

DROP_TABLE = '''
    DROP TABLE IF EXISTS account_account_tree_analysis
'''

SQL_ACCOUNT_TREE_ANALYSIS_TABLE = '''
create table account_account_tree_analysis as
select
  row_number() over() as id,
  *
from
  account_account_tree_analysis_view
order by
  child_account_id,
  parent_account_id;
'''


class FinancialPayreceive(models.TransientModel):
    _name = b'wizard.financial.cashflow'

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
    def _get_return_accounts_dict(self):
        """

        :return:
        """
        SQL_BUSCA = '''
                select
                    aa.code,
                    aa.name,
                    date_trunc('month', fm.{}) as Month,
                    sum(fm.amount_total * fm.sign)
                from
                    financial_move fm
                    join account_account_tree_analysis aat on aat.child_account_id =
                fm.account_id
                    join account_account aa on aa.id = aat.parent_account_id
                where
                    fm.type in ('2receive', '2pay')
                    and fm.{} >= '{}' and fm.{} <= '{}'
                group by
                    aa.code, aa.name, Month
                '''
        drop_view_if_exists(self._cr, 'account_account_tree_analysis_view')
        # drop_table_if_exists(self._cr, 'account_account_tree_analysis')
        self._cr.execute(DROP_TABLE)
        self._cr.execute(SQL_ACCOUNT_TREE_ANALYSIS_VIEW)
        self._cr.execute(SQL_ACCOUNT_TREE_ANALYSIS_TABLE)
        SQL_BUSCA = SQL_BUSCA.format(
            self.period, self.period, self.date_from,
            self.period, self.date_to
        )
        self.env.cr.execute(SQL_BUSCA)
        accounts_return = self.env.cr.dictfetchall()
        months = (fields.Datetime.from_string(self.date_to).month -
                  fields.Datetime.from_string(self.date_from).month) + 1
        report_dict = {
            'meses': [],
            'contas': {},
            'resumo': {},
            'saldo_final': [0.0] * months,
            'saldo_acumulado': [0.0] * months,
        }
        virada_ano = 0
        mes_ano = 0
        for i in range(0, months):
            report_dict['meses'].append(
                MONTH[
                    fields.Datetime.from_string(self.date_from).month + mes_ano
                    ] + str(
                    fields.Datetime.from_string(self.date_to).year + virada_ano
                )
            )
            mes_ano += 1
            if fields.Datetime.from_string(self.date_to).month == 12:
                virada_ano += 1
                mes_ano = 0
        for account_values in accounts_return:
            if not report_dict['contas'].get(account_values['code']):
                report_dict['contas'].update(
                    {
                        account_values['code']: {
                            'code': account_values['code'],
                            'name': account_values['name'],
                            'sum': [0.0] * months,
                        }
                    }
                )
                report_dict['contas'][account_values['code']]['sum'][0] = \
                    account_values['sum']
            else:
                report_dict['contas'][account_values['code']]['sum'][
                    next(
                        i for i, j in enumerate(
                            report_dict['contas'][
                                account_values['code']
                            ]['sum']
                        ) if not j
                    )
                ] = account_values['sum']
            if len(account_values['code']) == 1:
                if not report_dict['resumo'].get(account_values['name']):
                    report_dict['resumo'].update(
                        {
                            account_values['name']: {
                                'code': account_values['code'],
                                'name': account_values['name'],
                                'values': [0.0] * months,
                            }
                        }
                    )
                    report_dict['resumo'][account_values['name']][
                        'values'][0] = account_values['sum']
                else:
                    report_dict['resumo'][account_values['name']]['values'][
                        next(i for i, j in enumerate(
                            report_dict['resumo'][account_values['name']][
                                'values']) if
                             not j)
                    ] = account_values['sum']
        for resumo in report_dict['resumo']:
            report_dict['saldo_final'] = \
                [x + y for x, y in zip(
                    report_dict['saldo_final'],
                    report_dict['resumo'][resumo]['values']
                )]
        for i in range(0, months):
            if i == 0:
                report_dict['saldo_acumulado'][0] += \
                    report_dict['saldo_final'][0]
            else:
                report_dict['saldo_acumulado'][i] = \
                    report_dict['saldo_final'][i] + \
                    report_dict['saldo_acumulado'][i - 1]

        return report_dict

    @api.multi
    def doit(self):
        """
        Método disparado pela view
        :return:
        """
        report_dict = self._get_return_accounts_dict()
        report_dict2 = {
            'meses': [],
            'contas': [],
            'resumo': [],
        }
        report_dict2['meses'] = report_dict['meses']
        for account in report_dict['contas']:
            detalhes_conta = [report_dict['contas'][account]['code'], report_dict['contas'][account]['name']]
            report_dict2['contas'].append(detalhes_conta + report_dict['contas'][account]['sum'])
        for account_resumo in report_dict['resumo']:
            detalhes_resumo = [report_dict['resumo'][account_resumo]['code'], report_dict['resumo'][account_resumo]['name']]
            report_dict2['resumo'].append(detalhes_resumo + report_dict['resumo'][account_resumo]['values'])
        report_dict2['contas'] = sorted(report_dict2['contas'], key=itemgetter(0))
        report_dict2['resumo'] = sorted(report_dict2['resumo'], key=itemgetter(0))
        return True
