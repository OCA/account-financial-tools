# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class TrialBalanceXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(TrialBalanceXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('CashFlow')

    def _get_report_columns(self, report):
        row_mes = 2
        result ={
            0: {'header': _('Conta'), 'field': 'code', 'width': 12},
            1: {'header': _('Name'), 'field': 'name', 'width': 25},
        }

        meses = self.env.context['fluxo_de_caixa']['meses']
        for mes in sorted(meses):
            result.update({
                row_mes: {
                    'header': meses[mes].values()[0],
                    'field': 'dados',
                    'type': 'float',
                    'width': 15,
                    'mes_ano': meses[mes].keys()[0],
                },
            })
            row_mes += 1
        return result

    def _get_report_columns_resumo(self, report):
        # Coluna 0 e 1 São labels
        row_mes = 2
        # Dict que sera iterado as colunas dos labels
        result = {
            0: {'header': _('Conta'),
                'field': '0',
                'width': 12},
            1: {'header': _('Resumo'),
                'field': '1',
                'type': 'amount',
                'width': 25},
        }
        # Dict que sera iterado as colunas das contas (lines)
        for mes in self.env.context['fluxo_de_caixa']['meses']:
            result.update({
                row_mes: {'header': mes,
                          'field': row_mes,
                          'type': 'float',
                          'width': 15}
            })
            row_mes += 1
        return result

    def write_line(self, line_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.iteritems():

            # Pega o nome do field, e busca na linha pelo field
            value = line_object.get(column.get('field'))

            # Se for do tipo valor, deverá corresponder com mes-ano
            if column.get('type') == 'float':
                # Valor padrao para o float
                valor = 0.00
                # Para cada dado na linha com chave == mes-valor
                for mes_ano in value.iterkeys():

                    if column.get('mes_ano') == mes_ano:
                        valor = value[mes_ano]

                self.sheet.write_number(
                    self.row_pos, col_pos, valor, self.format_amount)

            # Se nao for float é string
            else:
                self.sheet.write_string(self.row_pos, col_pos, value or '')

        self.row_pos += 1

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def write_linha_soma(self):
        alfabeto = '.ABCDEFGHIJKLMNOPQRSTUVWYXZ'
        qtd_linhas = len(self.env.context['fluxo_de_caixa']['resumo'])
        for col_pos, column in self.columns.iteritems():
            if column.get('type') == 'float':
                celula = alfabeto[col_pos+1] + str(self.row_pos+1)
                formula = '{=SUM(%s%s:%s%s)}' % (
                    alfabeto[col_pos+1], str(self.row_pos-qtd_linhas),
                    alfabeto[col_pos+1], str(self.row_pos),
                )
                self.sheet.write_formula(celula, formula, self.format_amount)
            else:
                if col_pos == 1:
                    self.sheet.write_string(
                        self.row_pos, col_pos, 'SALDO' or '')
        self.row_pos += 1

    def write_linha_soma_acumulativa(self):
        alfabeto = '.ABCDEFGHIJKLMNOPQRSTUVWYXZ'
        primeira = True # Primeira celula da linha tem a formula diferenciada
        for col_pos, column in self.columns.iteritems():
            if column.get('type') == 'float':
                celula = alfabeto[col_pos+1] + str(self.row_pos+1)
                formula = '{=%s%s+%s%s}' % (
                    alfabeto[col_pos], str(self.row_pos+1),
                    alfabeto[col_pos+1], str(self.row_pos),
                )
                if primeira:
                    formula = '{=%s%s}' % (
                        alfabeto[col_pos+1], str(self.row_pos)
                    )
                    primeira = False
                self.sheet.write_formula(celula, formula, self.format_amount)
            else:
                if col_pos == 1:
                    self.sheet.write_string(
                        self.row_pos, col_pos, 'SALDO ACUMULATIVO' or '')
        self.row_pos += 1

    def _generate_report_content(self, workbook, report):

        # Set zoom
        self.sheet.set_zoom(85)

        # Display array header for account lines
        self.write_array_header()

        # For each account
        contas = self.env.context['fluxo_de_caixa']['contas']
        for account in sorted(contas.keys()):
            # Display account lines
            self.write_line(contas[account])

        # Cabeçalho do resumo
        self.write_array_header()
        contas_resumo = self.env.context['fluxo_de_caixa']['resumo']
        for resumo in sorted(contas_resumo.keys()):
            # Display resume
            self.write_line(contas_resumo[resumo])

        # Cria uma linha com formulas de SOMA para gerar Saldo
        self.write_linha_soma()

        # Cria um alinha com formulas de SOMA ACUMULANDO os valores do periodo anterior
        self.write_linha_soma_acumulativa()


TrialBalanceXslx(
    'report.financial.report_financial_cashflow_xlsx',
    'report_financial_cashflow',
    parser=report_sxw.rml_parse
)
