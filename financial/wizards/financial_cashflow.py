# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from __future__ import division, print_function, unicode_literals

from datetime import datetime

from operator import itemgetter

from odoo import api, fields, models


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


    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )

    period = fields.Selection(
        string='Period',
        required=True,
        default='date_maturity',
        selection=[
            ('date_maturity', 'Período Previsto'),
            ('date_payment', 'Período Realizado')
        ],
    )

    date_from = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-%m-01'),
    )
    date_to = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-12-01'),
    )

    hide_account_balance_at_0 = fields.Boolean(
        string='Hide account ending balance at 0',
        help='Use this filter to hide an account with an ending balance at 0.'
    )

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        return self._export(xlsx_report=True)

    def _prepare_dict(self):
        SQL_BUSCA = '''
            select
                fa.code,
                fa.name,
                date_trunc('month', fm.{period}) as Month,
                sum(fm.amount_total * fm.sign)
            from
                financial_move fm
                join financial_account_tree_analysis fat on fat.child_account_id = fm.account_id
                join financial_account fa on fa.id = fat.parent_account_id
            where
                fm.type {type} ('2receive', '2pay')
                and fm.{period} between '{date_from}' and '{date_to}'
            group by
                fa.code, fa.name, Month
        '''
        SQL_BUSCA = SQL_BUSCA.format(
            period=self.period,
            date_from=self.date_from,
            date_to=self.date_to,
            type='in' if self.period == 'date_maturity' else 'not in'
        )
        print(SQL_BUSCA)
        self.env.cr.execute(SQL_BUSCA)
        accounts_return = self.env.cr.dictfetchall()
        date_from = fields.Datetime.from_string(self.date_from)
        date_to = fields.Datetime.from_string(self.date_to)
        months = ((date_to.year - date_from.year) * 12 + \
                 date_to.month - date_from.month) + 1

        report_dict = {
            'meses': {},
            'contas': {},
            'resumo': {},
            'saldo_final': [0.0] * months,
            'saldo_acumulado': [0.0] * months,
        }
        virada_ano = 0
        mes = fields.Datetime.from_string(self.date_from).month
        ano = fields.Datetime.from_string(self.date_from).year
        meses = {}

        for i in range(0, months):
            key = str(mes) + '-' + str(ano + virada_ano)
            meses[i] = {
                key: MONTH[mes] + '/' + str(ano + virada_ano)
            }
            if mes == 12:
                virada_ano += 1
                mes = 0
            mes += 1

        def formata_dict(self, account_values):
            contas = {}
            for account_value in account_values:
                if not contas.get(account_value['code']):

                    contas = {
                        account_value['code']: {
                            'name': account_value['name'],
                            'code': account_value['code'],
                            'dados': {
                                'month_year': 0,
                            }
                        }
                    }

                    month_year =  \
                        str(account_value['month'].month) + '-' + \
                        str(account_value['month'].year)
                    contas[account_value['code']]['dados'][month_year] = \
                        account_value['value']
            return contas

        resumo = {}
        contas = {}
        for account_values in accounts_return:

            if not contas.get(account_values['code']):
                contas[account_values['code']] = {
                    'name': account_values['name'],
                    'code': account_values['code'],
                    'dados': {}
                }


            month_year = \
                str(account_values['month'].month) + '-' + \
                str(account_values['month'].year)
            contas[account_values['code']]['dados'][month_year] = \
                account_values['sum']

            if len(account_values['code']) == 1:
                if not resumo.get(account_values['code']):
                    resumo[account_values['code']] = {
                        'name': account_values['name'],
                        'code': account_values['code'],
                        'dados': {
                            'month_year': 0,
                        }
                    }
                month_year =  \
                    str(account_values['month'].month) + '-' + \
                    str(account_values['month'].year)
                resumo[account_values['code']]['dados'][month_year] = \
                    account_values['sum']

        report_dict['resumo'] = resumo
        report_dict['contas'] = contas
        report_dict['meses'] = meses


        # report_dict2 = dict(meses=[], contas=[], resumo=[])
        # report_dict2['meses'] = report_dict['meses']
        # for account in report_dict['contas']:
        #     detalhes_conta = [report_dict['contas'][account]['code'], report_dict['contas'][account]['name']]
        #     report_dict2['contas'].append(detalhes_conta + report_dict['contas'][account]['sum'])
        # for account_resumo in report_dict['resumo']:
        #     detalhes_resumo = [report_dict['resumo'][account_resumo]['code'], report_dict['resumo'][account_resumo]['name']]
        #     report_dict2['resumo'].append(detalhes_resumo + report_dict['resumo'][account_resumo]['values'])
        # report_dict2['contas'] = sorted(report_dict2['contas'], key=itemgetter(0))
        # report_dict2['resumo'] = sorted(report_dict2['resumo'], key=itemgetter(0))
        # report_dict2['saldo_final'] = report_dict['saldo_final']
        # report_dict2['saldo_acumulado'] = report_dict['saldo_acumulado']
        # from pprint import pprint
        # pprint (report_dict2)
        # # return report_dict2
        return report_dict

    def _prepare_report_trial_balance(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'hide_account_balance_at_0': self.hide_account_balance_at_0,
            'company_id': self.company_id.id,
        }

    def _export(self, xlsx_report=False):
        """Default export is PDF."""
        model = self.env['report_financial_cashflow']
        report = model.create(self._prepare_report_trial_balance())
        # print (self._prepare_dict())
        return \
            report.with_context(
                fluxo_de_caixa=self._prepare_dict()
            ).print_report(xlsx_report)
