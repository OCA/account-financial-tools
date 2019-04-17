# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Daniel Sadamo <daniel.sadamo@kmee.com.br>
#    Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from psycopg2.extensions import AsIs

from odoo import exceptions, fields, models, _


class ReportXslxFinancialPartnerStatement(models.AbstractModel):

    _name = 'report.financial.partner_statement'
    _inherit = 'report.finacial.base'

    def define_title(self):
        partner_name = self.report_wizard.partner_id.name
        if self.report_wizard.type == '2receive':
            partner_type = 'Customer'
        else:
            partner_type = 'Supplier'
        return _('%s Statement - %s' % (partner_type, partner_name))

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
            'moves': [],
            'moves_lines': [],
            'total_lines': {
                'total_vlr_bruto': 0.00,
                'total_vlr': 0.00,
                'total_saldo_dev': 0.00,
                'total_valor_rec': 0.00,
                'total_desc': 0.00,
                'total_multa': 0.00,
                'total_juros': 0.00,
                'total_rec': 0.00,
            },
        }

        SQL_INICIAL_VALUE = '''
            SELECT
               fm.id,
               fm.date_document,
               fm.document_number,
               fm.date_business_maturity,
               COALESCE(fm.amount_document, 0.0),
               COALESCE(fm.amount_paid_document, 0.0),
               fm.arrears_days,
               COALESCE(fm.amount_residual, 0.0),
               fm.partner_id,
               fm.debt_status,
               COALESCE(fm.amount_paid_total)
            FROM
              financial_move fm
            WHERE
              fm.type = %(type)s
              and fm.date_business_maturity between %(date_from)s and
               %(date_to)s
              and fm.partner_id = %(partner_id)s
            ORDER BY
              fm.date_business_maturity
        '''
        filters = {
            'partner_id': self.report_wizard.partner_id.id,
            'type': self.report_wizard.type,
            'date_to': self.report_wizard.date_to,
            'date_from': self.report_wizard.date_from,
        }
        self.env.cr.execute(SQL_INICIAL_VALUE, filters)
        data = self.env.cr.fetchall()
        if not data:
            raise exceptions.UserError(
                _('Não encontrado movimentações.')
            )
        move_ids = []
        for line in data:
            move_dict = {
                'move_id': line[0],
                'date_document': line[1],
                'document_number': line[2],
                'date_business_maturity': line[3],
                'amount_document': line[4],
                'amount_paid': line[5],
                'arrears_days': line[6],
                'amount_residual': line[7],
                'partner_id': line[8],
                'debt_status': line[9],
                'amount_total': line[10],
            }
            move_ids.append(line[0])
            report_data['total_lines']['total_vlr_bruto'] += float(line[4])
            report_data['total_lines']['total_vlr'] += float(line[5])
            report_data['total_lines']['total_saldo_dev'] += float(line[7])

            SQL_VALUE = '''
                SELECT
                   COALESCE(fm.amount_paid_document, 0.0),
                   COALESCE(fm.amount_paid_discount, 0.0),
                   COALESCE(fm.amount_paid_penalty, 0.0),
                   COALESCE(fm.amount_paid_interest, 0.0),
                   fm.date_payment,
                   COALESCE(fm.amount_total, 0.0),
                   fm.debt_status,
                   fm.debt_id
                FROM
                  financial_move fm
                WHERE
                  fm.debt_id = %(debt_id)s ;
            '''
            filters = {
                'debt_id': AsIs(str(line[0]).replace(',)', ')')),
            }
            self.env.cr.execute(SQL_VALUE, filters)
            data2 = self.env.cr.fetchall()
            for line in data2:
                line_dict = {
                    'amount_paid': line[0] or 0.0,
                    'amount_discount': line[1] or 0.0,
                    'amount_penalty_forecast': line[2] or 0.0,
                    'amount_interest_forecast': line[3] or 0.0,
                    'date_payment': line[4],
                    'amount_total': line[5] or 0.0,
                    'debt_status': line[6],
                }
                move_dict['payment_lines'] = line_dict
                report_data['total_lines']['total_valor_rec'] += float(line[0])
                report_data['total_lines']['total_desc'] += float(line[1])
                report_data['total_lines']['total_multa'] += float(line[2])
                report_data['total_lines']['total_juros'] += float(line[3])
                report_data['total_lines']['total_rec'] += float(line[5])

            report_data['moves'].append(move_dict)

        SQL_MOVE_LINE_VALUE = '''
            SELECT
               fm.id,
               fm.date_document,
               fm.document_number,
               fm.date_business_maturity,
               COALESCE(fm.amount_document, 0.0),
               COALESCE(fm.amount_interest, 0.0),
               COALESCE(fm.amount_penalty, 0.0),
               COALESCE(fm.amount_discount, 0.0),
               fm.arrears_days,
               COALESCE(fm.amount_residual, 0.0),
               fm.partner_id,
               fm.debt_id,
               fm.date_payment,
               COALESCE(fm.amount_total, 0.0)
            FROM
              financial_move fm
            WHERE
              fm.debt_id in %(move_ids)s
            ORDER BY
              fm.debt_id
                '''
        filters = {
            'partner_id': self.report_wizard.partner_id.id,
            'type': self.report_wizard.type,
            'date_to': self.report_wizard.date_to,
            'date_from': self.report_wizard.date_from,
            'move_ids': AsIs(str(tuple(move_ids)).replace(',)',')')),
        }
        self.env.cr.execute(SQL_MOVE_LINE_VALUE, filters)
        data_move_lines = self.env.cr.fetchall()
        for line in data_move_lines:
            move_line_dict = {
                'amount_paid_receipt_item': line[4],
                'amount_discount': line[7],
                'amount_penalty_forecast': line[6],
                'amount_interest_forecast': line[5],
                'date_payment': line[12],
                'move_id': line[0],
                'debt_id': line[11],
                'amount_total': line[13],
            }
            report_data['moves_lines'].append(move_line_dict)
            report_data['total_lines']['total_desc'] += float(line[7])
            report_data['total_lines']['total_multa'] += float(line[6])
            report_data['total_lines']['total_juros'] += float(line[5])
        return report_data

    def define_columns(self):
        result = {
            0: {
                'header': _('Data Documento'),
                'field': 'document_date',
                'width': 20,
                'style': 'date',
                'type': 'date'
            },
            1: {
                'header': _('Nº Documento'),
                'field': 'document_number',
                'width': 25,
                'style': self.style.detail_center.align_center,
            },
            2: {
                'header': _('Vencimento'),
                'field': 'date_business_maturity',
                'width': 20,
                'style': 'date',
                'type': 'date'
            },
            3: {
                'header': _('Valor Bruto'),
                'field': 'amount_document',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            4: {
                'header': _('Valor Pago'),
                'field': 'amount_paid',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            5: {
                'header': _('Atraso'),
                'field': 'arrears_days',
                'width': 20,
            },
            6: {
                'header': _('Saldo Devido'),
                'field': 'amount_residual',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            #
            # RECEBIMENTO/BAIXA
            #
            7: {
                'header': _('Valor'),
                'field': 'amount_paid_receipt_item',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            8: {
                'header': _('Desc.'),
                'field': 'amount_discount',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            9: {
                'header': _('Multa'),
                'field': 'amount_penalty_forecast',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            10: {
                'header': _('Juros'),
                'field': 'amount_interest_forecast',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            11: {
                'header': _('Data Recebimento'),
                'field': 'date_payment',
                'width': 20,
                'style': 'date',
                'type': 'date',
            },
            12: {
                'header': _('Total Recebido'),
                'field': 'amount_total',
                'width': 20,
                'style': 'currency',
                'type': 'currency'
            },
            13: {
                'header': _('Status'),
                'field': 'debt_status',
                'width': 20,
                'style': self.style.detail_center.align_center,
            },
        }

        return result

    def define_total_columns(self):
        result = {
            3: {
                'header': _('Valor Bruto'),
                'field': 'amount_document',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            4: {
                'header': _('Valor Pago'),
                'field': 'amount_paid',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            6: {
                'header': _('Saldo Devido'),
                'field': 'amount_residual',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            7: {
                'header': _('Valor'),
                'field': 'amount_paid_receipt_item',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            8: {
                'header': _('Desc.'),
                'field': 'amount_discount',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            9: {
                'header': _('Multa'),
                'field': 'amount_penalty_forecast',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            10: {
                'header': _('Juros'),
                'field': 'amount_interest_forecast',
                'width': 20,
                'style': 'currency',
                'type': 'currency',
            },
            12: {
                'header': _('Total Recebido'),
                'field': 'amount_total',
                'width': 20,
                'style': 'currency',
                'type': 'currency'
            },
        }

        return result

    def write_content(self):
        self.sheet.set_zoom(85)
        self.sheet.merge_range(
            self.current_row, 0,
            self.current_row + 1,
            6,
            _('Lançamentos'),
            self.style.header.align_center
        )
        self.sheet.merge_range(
            self.current_row, 7,
            self.current_row + 1,
            len(self.columns) - 1,
            _('Recebimentos / Baixa'),
            self.style.header.align_center
        )
        self.current_row += 2
        self.write_header()
        for move_id in self.report_data['moves']:
            move_dict = {
                'document_date': move_id[u'date_document'],
                'document_number': move_id[u'document_number'],
                'date_business_maturity': move_id[u'date_business_maturity'],
                'amount_document': move_id[u'amount_document'],
                'amount_paid': move_id[u'amount_total'],
                'arrears_days': move_id[u'arrears_days'],
                'amount_residual': move_id[u'amount_residual'],
                'debt_status': move_id[u'debt_status'],
                'amount_paid_receipt_item': 0,
                'amount_discount': 0,
                'amount_penalty_forecast': 0,
                'amount_interest_forecast': 0,
                'date_payment': '',
                'amount_total': 0,

            }
            self.write_detail(move_dict)
            cont = 0
            for move_line_id in self.report_data['moves_lines']:
                if move_line_id['debt_id'] == move_id['move_id']:
                    move_line_dict = {
                        'document_date': '',
                        'document_number': '',
                        'date_business_maturity': '',
                        'amount_document': 0,
                        'amount_paid_receipt_item':
                            move_line_id['amount_paid_receipt_item'],
                        'arrears_days': move_line_id['amount_discount'],
                        'amount_residual': 0,
                        'amount_discount': move_line_id[u'amount_discount'],
                        'amount_penalty_forecast':
                            move_line_id['amount_penalty_forecast'],
                        'amount_interest_forecast':
                            move_line_id['amount_interest_forecast'],
                        'date_payment': move_line_id[u'date_payment'],
                        'amount_total': move_line_id[u'amount_total'],
                        'debt_status': '',
                        'amount_paid': 0,
                    }
                    self.write_detail(move_line_dict)
                    # del self.report_data['moves_lines'][cont]
                cont += 1
        self.sheet.merge_range(
            self.current_row, 0,
            self.current_row + 1,
            len(self.columns) - 1,
            _('Total Geral'),
            self.style.header.align_left
        )
        self.current_row += 2
        self.write_header()
        first_data_row = self.current_row + 1
        total_columns = self.define_total_columns()
        total_dict = {
            'amount_document':
                self.report_data['total_lines']['total_vlr_bruto'],
            'amount_paid_receipt_item':
                self.report_data['total_lines']['total_valor_rec'],
            'amount_residual':
                self.report_data['total_lines']['total_saldo_dev'],
            'amount_discount': self.report_data['total_lines']['total_desc'],
            'amount_penalty_forecast':
                self.report_data['total_lines']['total_multa'],
            'amount_interest_forecast':
                self.report_data['total_lines']['total_juros'],
            'amount_total': self.report_data['total_lines']['total_vlr'],
            'amount_paid': self.report_data['total_lines']['total_rec'],
        }
        self.write_detail(
            total_dict, total_columns, first_data_row
        )

    def generate_xlsx_report(self, workbook, data, report_wizard):
        super(ReportXslxFinancialPartnerStatement, self).generate_xlsx_report(
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
