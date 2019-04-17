# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Aristides Caldeira <aristides.caldeira@kmee.com.br>
#    Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from six import string_types
from odoo import fields
from odoo import models
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract

from decimal import Decimal


class ReportXlsxStyle(object):

    def __init__(self, *args, **kwargs):
        self.align_left = None
        self.date = None
        self.time = None
        self.align_center = None
        self.align_right = None
        self.integer = None
        self.float = None
        self.percentage = None
        self.currency = None


def _col_number_to_reference(col):
    return chr(ord('A') + col)


def col_number_to_reference(col):
    if col >= 26:
        quotient, remaining = divmod(col, 26)
        return _col_number_to_reference(quotient - 1) + \
            col_number_to_reference(remaining)

    return _col_number_to_reference(col)


class ReportXlsxFinancialBase(models.AbstractModel):

    _name = 'report.finacial.base'
    _inherit = 'report.report_xlsx.abstract'

    def __init__(self, *opts, **attrs):
        self.current_row = 1
        super(ReportXlsxFinancialBase, self).__init__(*opts, **attrs)

    def get_workbook_options(self):
        return {'constant_memory': True}

    def generate_xlsx_report(self, workbook, data, report_wizard):
        self.report_wizard = report_wizard
        self.workbook = workbook

        self.current_row = 0
        self.title = self.define_title()
        self.sheet = \
            self.workbook.add_worksheet(self.title[:31])
        self.define_styles()
        self.report_data = self.prepare_data()
        self.columns = self.define_columns()
        self._set_column_width()
        self.write_title()
        self.write_filters()
        self.write_content()

    def define_default_style(self):
        return {
            'font_name': 'Calibri',
            'font_size': '11',
            'font_color': '#000000',
            'align': 'vjustify',
            'valign': 'top',
        }

    def define_title_default_style(self):
        style = self.define_default_style()
        style.update({
            'bold': True,
            'border': True,
            'bg_color': '#DEDEDE',
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 30,
        })
        return style

    def define_filter_default_style(self):
        style = self.define_default_style()
        style.update({
            'bold': True,
            'bg_color': '#DEDEDE',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
        })
        return style

    def define_group_header_default_style(self):
        style = self.define_default_style()
        style.update({
            'bold': True,
            'bg_color': '#DEDEDE',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
        })
        return style

    def define_header_default_style(self):
        style = self.define_default_style()
        style.update({
            'bold': True,
            'bg_color': '#DEDEDE',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
        })
        return style

    def define_detail_default_style(self):
        return self.define_default_style()

    def define_detail_center_default_style(self):
        style = self.define_default_style()
        style.update({
            'align': 'center',
            'valign': 'vcenter',
        })
        return style

    def define_footer_default_style(self):
        style = self.define_default_style()
        style.update({
            'bold': True,
            'bg_color': '#DEDEDE',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
        })
        return style

    def define_group_footer_default_style(self):
        style = self.define_default_style()
        style.update({
            'bold': True,
            'bg_color': '#DEDEDE',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
        })
        return style

    def define_default_styles(self, style, default_style):
        style.align_left = self.workbook.add_format(dict(default_style))
        default_style['num_format'] = 'dd/mm/yyyy'
        style.date = self.workbook.add_format(dict(default_style))
        default_style['num_format'] = 'hh:mm'
        style.time = self.workbook.add_format(dict(default_style))

        #
        # Center aligned styles
        #
        default_style['align'] = 'center'
        default_style['num_format'] = ''
        style.align_center = self.workbook.add_format(dict(default_style))

        #
        # Right aligned styles
        #
        default_style['align'] = 'right'
        default_style['num_format'] = None
        style.align_right = self.workbook.add_format(dict(default_style))
        default_style['num_format'] = '#,##0;-#,##0'
        style.integer = self.workbook.add_format(dict(default_style))
        default_style['num_format'] = '#,##0.00;-#,##0.00'
        style.float = self.workbook.add_format(dict(default_style))
        default_style['num_format'] = '#,##0.00%'
        style.percentage = self.workbook.add_format(dict(default_style))
        default_style['num_format'] = \
            '[$R$-416] #,##0.00;[RED]-[$R$-416] #,##0.00'
        style.currency = self.workbook.add_format(dict(default_style))

    def define_styles(self):
        self.style = ReportXlsxStyle()
        self.style.title = ReportXlsxStyle()
        self.style.filter = ReportXlsxStyle()
        self.style.group_header = ReportXlsxStyle()
        self.style.header = ReportXlsxStyle()
        self.style.detail = ReportXlsxStyle()
        self.style.detail_center = ReportXlsxStyle()
        self.style.footer = ReportXlsxStyle()
        self.style.group_footer = ReportXlsxStyle()

        self.define_default_styles(self.style.title,
                                   self.define_title_default_style())
        self.define_default_styles(self.style.filter,
                                   self.define_filter_default_style())
        self.define_default_styles(self.style.group_header,
                                   self.define_group_header_default_style())
        self.define_default_styles(self.style.header,
                                   self.define_header_default_style())
        self.define_default_styles(self.style.detail,
                                   self.define_detail_default_style())
        self.define_default_styles(self.style.detail_center,
                                   self.define_detail_center_default_style())
        self.define_default_styles(self.style.footer,
                                   self.define_footer_default_style())
        self.define_default_styles(self.style.group_footer,
                                   self.define_group_footer_default_style())

    def _set_column_width(self):
        for position, column in iter(self.columns.items()):
            self.sheet.set_column(position, position, column['width'])

    def write_title(self):
        self.sheet.merge_range(
            self.current_row, 0, self.current_row + 2, len(self.columns) - 1,
            self.title, self.style.title.align_center
        )
        self.current_row += 3

    def write_filters(self):
        filters = self.define_filters()
        filter_title_column_span = self.define_filter_title_column_span()
        filter_value_column_span = self.define_filter_value_column_span()

        title_column = 1
        value_column = title_column + filter_title_column_span + 1

        self.current_row += 1

        for position, filter in iter(filters.items()):
            title = filter['title']
            value = filter['value']
            style = filter.get('style', self.style.header.align_left)

            self.sheet.merge_range(
                self.current_row, title_column,
                self.current_row, title_column + filter_title_column_span - 1,
                title, self.style.header.align_left)

            self.sheet.merge_range(
                self.current_row, value_column,
                self.current_row, value_column + filter_value_column_span - 1,
                value, style)

            self.current_row += 1

        self.current_row += 1

    def write_header(self, columns=None):
        if columns is None:
            columns = self.columns

        for current_column, column in iter(columns.items()):
            self.sheet.write(self.current_row, current_column,
                             column['header'], self.style.header.align_center)
        self.current_row += 1

    def write_detail(self, line, columns=None, last_row=None,
                     formula_changes=None):

        if formula_changes is None:
            formula_changes = {}
        if columns is None:
            columns = self.columns
        if last_row is None:
            first_row = self.current_row
        else:
            first_row = last_row

        first_column = list(self.columns.keys())[0]
        last_column = list(self.columns.keys())[-1]
        if last_column >= 1:
            penultimate_column = last_column - 1
        else:
            penultimate_column = first_column

        for current_column, column in iter(columns.items()):
            style = column.get('style', self.style.detail.align_left)

            if isinstance(style, string_types):
                style = getattr(self.style.detail, style,
                                self.style.detail.align_left)

            if isinstance(line, dict):
                value = line.get(column['field'])
            else:
                value = getattr(line, column['field'])

            if column.get('type', 'string') == 'formula':
                change = {
                    'first_row': first_row,
                    'current_row': self.current_row + 1,
                    'previous_row': self.current_row,

                    'first_column': col_number_to_reference(first_column),
                    'current_column': col_number_to_reference(current_column),
                    'last_column': col_number_to_reference(last_column),
                    'penultimate_column':
                        col_number_to_reference(penultimate_column),
                    'previous_column':
                        col_number_to_reference(current_column - 1),
                }
                change.update(formula_changes)
                value = column.get('formula', value)
                value = value.format(**change)
                value = '{' + value + '}'
                self.sheet.write_formula(
                    self.current_row, current_column, value, style)

            elif column.get('type', 'string') in \
                    ('int', 'float', 'decimal', 'Decimal',
                     'currency', 'amount') or \
                    isinstance(value, (int, float, Decimal)):
                self.sheet.write_number(self.current_row, current_column,
                                        value, style)
            elif column.get('type', 'string') == 'date':
                self.sheet.write(
                    self.current_row, current_column,
                    fields.Date.from_string(value), style
                )
            else:
                self.sheet.write(self.current_row, current_column,
                                 value or '', style)

        self.current_row += 1

    def write_content(self):
        pass

    def define_title(self):
        return 'You did not define the report title!'

    def define_columns(self):
        """
            Allow to define the report columns
            which will be used to generate report.

            :return: the report columns as dict

            :Example:

            {
                0: {
                    'title': 'Simple column',
                    'field': 'field_name_on_my_object',
                    'width': 11,
                },
                1: {
                    'title': 'Amount column',
                    'field': 'field_name_on_my_object',
                    'style': self.style.detail.amount,
                    'width': 14,
                },
            }
        """
        return {}

    def define_filters(self):
        '''
        :return: Defines report filters as dictionaries

        :Example:

        {
            0: {
                'title': 'Filter "human" name',
                'value': filter value,
                'style': filter value style,
            }
        }
        '''
        return {}

    def define_filter_title_column_span(self):
        return 1

    def define_filter_value_column_span(self):
        return 1

    def prepare_report_data(self):
        return {}
