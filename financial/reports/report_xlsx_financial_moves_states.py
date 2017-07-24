# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from psycopg2.extensions import AsIs

from dateutil.relativedelta import relativedelta
from openerp import _
from openerp import fields
from openerp.report import report_sxw

from .report_xlsx_financial_base import ReportXlsxFinancialBase


class ReportXslxFinancialMovesStates(ReportXlsxFinancialBase):
    def define_title(self):
        if self.report_wizard.group_by == 'maturity':
            title = _('Fiscal Moves by Maturity')
        else:
            title = _('Fiscal Moves by Partner')

        return title

    def define_filters(self):
        date_from = fields.Datetime.from_string(self.report_wizard.date_from)
        date_from = date_from.date()
        date_to = fields.Datetime.from_string(self.report_wizard.date_to)
        date_to = date_to.date()

        filters = {
            0: {
                'title': _('Date'),
                'value': _('From %s to %s') %
                (date_from.strftime('%d/%m/%Y'),
                 date_to.strftime('%d/%m/%Y')),
            },
            1: {
                'title': _('Company'),
                'value': self.report_wizard.company_id.name,
            },

        }
        return filters

    def define_filter_title_column_span(self):
        return 2

    def define_filter_value_column_span(self):
        return 3

    def prepare_data(self):
        #
        # First, we prepare the report_data lines, time_span and accounts
        #
        report_data = {
            # 'cod_conta': {},
            # 'conta': {},
            # 'num_documento': {},
            # 'dt_doc': {},
            # 'dt_venc': {},
            # 'dt_quit': {},
            # 'prov': {},
            # 'vlr_original': {},
            # 'desc': {},
            # 'multa': {},
            # 'juros': {},
            # 'parc_total': {},
            'lines': {},
        }

        date_from = fields.Datetime.from_string(self.report_wizard.date_from)
        date_from = date_from.date()
        date_to = fields.Datetime.from_string(self.report_wizard.date_to)
        date_to = date_to.date()

        SQL_INICIAL_VALUE = '''
            SELECT 
               fm.id,
               fa.code,
               fa.name,
               fm.document_number,
               fm.date_document,
               fm.date_business_maturity,
               fm.date_payment,
               fm.amount_document,
               fm.amount_paid_discount,
               fm.amount_paid_penalty,
               fm.amount_paid_interest,
               fm.amount_paid_total
            FROM 
              financial_move fm
              join financial_account fa on fa.id = fm.account_id
            WHERE
              fm.type = '2pay' and fm.state = 'open';
        '''
        self.env.cr.execute(SQL_INICIAL_VALUE)
        data = self.env.cr.fetchall()
        for line in data:
            line_dict = {
                'cod_conta': line[1],
                'conta': line[2],
                'num_documento': line[3],
                'dt_doc': line[4],
                'dt_venc': line[5],
                'dt_quit': line[6],
                # 'prov': line[7],
                'vlr_original': line[7],
                'desc': line[8],
                'multa': line[9],
                'juros': line[10],
                'parc_total': line[11],
            }
            report_data['lines'][line[0]] = line_dict

        return report_data

    def define_columns(self):
        result = {
            0: {
                'header': _('Cod. Conta'),
                'field': 'cod_conta',
                'width': 12,
            },
            1: {
                'header': _('Conta'),
                'field': 'conta',
                'width': 25,
            },
            2: {
                'header': _('Nº Documento'),
                'field': 'num_documento',
                'width': 20,
            },
            3: {
                'header': _('Dt. Doc.'),
                'field': 'dt_doc',
                'width': 20,
            },
            4: {
                'header': _('Dt. Venc.'),
                'field': 'dt_venc',
                'width': 20,
            },
            5: {
                'header': _('Dt. Quit.'),
                'field': 'dt_quit',
                'width': 20,
            },
            6: {
                'header': _('Prov.'),
                'field': 'prov',
                'width': 20,
            },
            7: {
                'header': _('Vlr. Original'),
                'field': 'vlr_original',
                'width': 20,
            },
            8: {
                'header': _('Desc.'),
                'field': 'desc',
                'width': 20,
            },
            9: {
                'header': _('Multa'),
                'field': 'multa',
                'width': 20,
            },
            10: {
                'header': _('Juros'),
                'field': 'juros',
                'width': 20,
            },
            11: {
                'header': _('Parc./Total'),
                'field': 'parc_total',
                'width': 20,
            },
        }

        return result

    def write_content(self):
        self.sheet.set_zoom(85)
        self.write_header()
        for move_id in sorted(self.report_data['lines'].keys()):
            self.write_detail(self.report_data['lines'][move_id])

    def generate_xlsx_report(self, workbook, data, report_wizard):
        super(ReportXslxFinancialMovesStates, self).generate_xlsx_report(
            workbook, data, report_wizard)

        workbook.set_properties({
            'title': self.title,
            'company': self.report_wizard.company_id.name,
            'comments': _('Created with Financial app on {now}').format(
                now=fields.Datetime.now())
        })

        #
        # Documentation for formatting pages here:
        # http://xlsxwriter.readthedocs.io/page_setup.html
        #
        self.sheet.set_landscape()
        self.sheet.set_paper(9)  # A4
        self.sheet.fit_to_pages(1, 99999)
        #
        # Margins, in inches, left, right, top, bottom;
        # 1 / 2.54 = 1 cm converted in inches
        #
        self.sheet.set_margins(1 / 2.54, 1 / 2.54, 1 / 2.54, 1 / 2.54)


ReportXslxFinancialMovesStates(
    #
    # Name of the report in report_xlsx_financial_cashflow_data.xml,
    # field name, *always* preceeded by "report."
    #
    'report.report_xlsx_financial_moves_states',
    #
    # The model used to filter report data, or where the data come from
    #
    'report.xlsx.financial.moves.states.wizard',
    parser=report_sxw.rml_parse
)
