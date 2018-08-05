# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
    import AbstractReportXlsx
from odoo.exceptions import UserError
from odoo.report import report_sxw
from odoo.tools.translate import translate, _

_logger = logging.getLogger(__name__)


IR_TRANSLATION_NAME = 'account.asset.report'


class AssetReportXlsx(AbstractReportXlsx):

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, wb, data, wiz):
        self.assets = self._get_children(wiz)
        s1 = self._get_acquisition_ws_params(wb, data, wiz)
        s2 = self._get_active_ws_params(wb, data, wiz)
        s3 = self._get_removal_ws_params(wb, data, wiz)
        return [s1, s2, s3]

    def _get_asset_template(self):

        asset_template = {
            'account': {
                'header': {
                    'type': 'string',
                    'value': self._('Account'),
                },
                'asset': {
                    'type': 'string',
                    'value': self._render(
                        "asset.profile_id.account_asset_id.code"),
                },
                'totals': {
                    'type': 'string',
                    'value': self._('Totals'),
                },
                'width': 20,
            },
            'name': {
                'header': {
                    'type': 'string',
                    'value': self._('Name'),
                },
                'asset_view': {
                    'type': 'string',
                    'value': self._render("asset.name"),
                },
                'asset': {
                    'type': 'string',
                    'value': self._render("asset.code or ''"),
                },
                'width': 40,
            },
            'code': {
                'header': {
                    'type': 'string',
                    'value': self._('Reference'),
                },
                'asset_view': {
                    'type': 'string',
                    'value': self._render("asset.code or ''"),
                },
                'asset': {
                    'type': 'string',
                    'value': self._render("asset.code or ''"),
                },
                'width': 20,
            },
            'date_start': {
                'header': {
                    'type': 'string',
                    'value': self._('Asset Start Date'),
                },
                'asset_view': {},
                'asset': {
                    'value': self._render(
                        "asset.date_start and "
                        "datetime.strptime(asset.date_start,'%Y-%m-%d') "
                        "or None"),
                    'format': self.format_tcell_date_left,
                },
                'width': 20,
            },
            'date_remove': {
                'header': {
                    'type': 'string',
                    'value': self._('Asset Removal Date'),
                },
                'asset': {
                    'value': self._render(
                        "asset.date_remove and "
                        "datetime.strptime(asset.date_remove,'%Y-%m-%d') "
                        "or None"),
                    'format': self.format_tcell_date_left,
                },
                'width': 20,
            },
            'depreciation_base': {
                'header': {
                    'type': 'string',
                    'value': self._('Depreciation Base'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_view': {
                    'type': 'formula',
                    'value': self._render("asset_formula"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'number',
                    'value': self._render("asset.depreciation_base"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('asset_total_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'salvage_value': {
                'header': {
                    'type': 'string',
                    'value': self._('Salvage Value'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_view': {
                    'type': 'formula',
                    'value': self._render("salvage_formula"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'number',
                    'value': self._render("asset.salvage_value"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('salvage_total_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'fy_start_value': {
                'header': {
                    'type': 'string',
                    'value': self._('FY Start Value'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_view': {
                    'type': 'formula',
                    'value': self._render("fy_start_formula"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'number',
                    'value': self._render("asset.fy_start_value"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('fy_start_total_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'fy_depr': {
                'header': {
                    'type': 'string',
                    'value': self._('FY Depreciation'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_view': {
                    'type': 'formula',
                    'value': self._render("fy_diff_formula"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'formula',
                    'value': self._render("fy_diff_formula"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('fy_diff_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'fy_end_value': {
                'header': {
                    'type': 'string',
                    'value': self._('FY End Value'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_view': {
                    'type': 'formula',
                    'value': self._render("fy_end_formula"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'number',
                    'value': self._render("asset.fy_end_value"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('fy_end_total_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'fy_end_depr': {
                'header': {
                    'type': 'string',
                    'value': self._('Tot. Depreciation'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_view': {
                    'type': 'formula',
                    'value': self._render("total_depr_formula"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'formula',
                    'value': self._render("total_depr_formula"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('total_depr_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'method': {
                'header': {
                    'type': 'string',
                    'value': self._('Comput. Method'),
                    'format': self.format_theader_yellow_center,
                },
                'asset': {
                    'type': 'string',
                    'value': self._render("asset.method or ''"),
                    'format': self.format_tcell_center,
                },
                'width': 20,
            },
            'method_number': {
                'header': {
                    'type': 'string',
                    'value': self._('Number of Years'),
                    'format': self.format_theader_yellow_center,
                },
                'asset': {
                    'type': 'number',
                    'value': self._render("asset.method_number"),
                    'format': self.format_tcell_integer_center,
                },
                'width': 20,
            },
            'prorata': {
                'header': {
                    'type': 'string',
                    'value': self._('Prorata Temporis'),
                    'format': self.format_theader_yellow_center,
                },
                'asset': {
                    'type': 'boolean',
                    'value': self._render("asset.prorata"),
                    'format': self.format_tcell_center,
                },
                'width': 20,
            },
        }
        asset_template.update(
            self.env['account.asset']._xls_asset_template())

        return asset_template

    def _get_acquisition_ws_params(self, wb, data, wiz):

        acquisition_template = self._get_asset_template()
        acquisition_template.update(
            self.env['account.asset']._xls_acquisition_template())
        wl_acq = self.env['account.asset']._xls_acquisition_fields()
        title = self._get_title(wiz, 'acquisition', format='normal')
        title_short = self._get_title(wiz, 'acquisition', format='short')
        sheet_name = title_short[:31].replace('/', '-')

        return {
            'ws_name': sheet_name,
            'generate_ws_method': '_acquisition_report',
            'title': title,
            'wanted_list': wl_acq,
            'col_specs': acquisition_template,
        }

    def _get_active_ws_params(self, wb, data, wiz):

        active_template = self._get_asset_template()
        active_template.update(
            self.env['account.asset']._xls_active_template())
        wl_act = self.env['account.asset']._xls_active_fields()
        title = self._get_title(wiz, 'active', format='normal')
        title_short = self._get_title(wiz, 'active', format='short')
        sheet_name = title_short[:31].replace('/', '-')

        return {
            'ws_name': sheet_name,
            'generate_ws_method': '_active_report',
            'title': title,
            'wanted_list': wl_act,
            'col_specs': active_template,
        }

    def _get_removal_ws_params(self, wb, data, wiz):

        removal_template = self._get_asset_template()
        removal_template.update(
            self.env['account.asset']._xls_removal_template())
        wl_dsp = self.env['account.asset']._xls_removal_fields()
        title = self._get_title(wiz, 'removal', format='normal')
        title_short = self._get_title(wiz, 'removal', format='short')
        sheet_name = title_short[:31].replace('/', '-')

        return {
            'ws_name': sheet_name,
            'generate_ws_method': '_removal_report',
            'title': title,
            'wanted_list': wl_dsp,
            'col_specs': removal_template,
        }

    def _get_title(self, wiz, report, format='normal'):
        period = wiz.date_range_id
        if format == 'short':
            prefix = period.name
        else:
            if period.type_id.fiscal_year:
                prefix = _('Fiscal Year') + ' %s' % period.name
            else:
                prefix = '%s - %s' % (period.date_start, period.date_end)
        if report == 'acquisition':
            if format == 'normal':
                suffix = ' : ' + _('New Acquisitions')
            else:
                suffix = '-ACQ'
        elif report == 'active':
            if format == 'normal':
                suffix = ' : ' + _('Active Assets')
            else:
                suffix = '-ACT'
        else:
            if format == 'normal':
                suffix = ' : ' + _('Removed Assets')
            else:
                suffix = '-DSP'
        return prefix + suffix

    def _report_title(self, ws, row_pos, ws_params, data, wiz):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _empty_report(self, ws, row_pos, ws_params, data, wiz, report):
        if report == 'acquisition':
            suffix = _('New Acquisitions')
        elif report == 'active':
            suffix = _('Active Assets')
        else:
            suffix = _('Removed Assets')
        no_entries = _("No") + " " + suffix
        ws.write_string(row_pos, 0, no_entries, self.format_left_bold)

    def _get_children(self, wiz):
        parent = wiz.parent_asset_id

        def _child_get(parent):
            assets = self.env['account.asset']
            children = parent.child_ids.filtered(lambda r: r.state != 'draft')
            children = children.sorted(lambda r: (r.date_start, r.code))
            for child in children:
                assets += child
                assets += _child_get(child)
            return assets

        assets = parent + _child_get(parent)
        return assets

    def _view_add(self, acq, assets):
        parent = self.assets.filtered(lambda r: acq.parent_id == r)
        if parent and parent not in assets:
            self._view_add(parent, assets)
        assets.append(acq)

    def _acquisition_report(self, workbook, ws, ws_params, data, wiz):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        wl_acq = ws_params['wanted_list']
        if 'account' not in wl_acq:
            raise UserError(_(
                "The 'account' field is a mandatory entry of the "
                "'_xls_acquisition_fields' list !"))

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._report_title(ws, row_pos, ws_params, data, wiz)

        acquisitions = self.env['account.asset'].search(
            [('date_start', '>=', wiz.date_range_id.date_start),
             ('date_start', '<=', wiz.date_range_id.date_end),
             ('type', '=', 'normal'),
             ('id', 'in', self.assets.ids)],
            order='date_start ASC')

        if not acquisitions:
            return self._empty_report(
                ws, row_pos, ws_params, data, wiz, 'acquisition')

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        row_pos_start = row_pos
        depreciation_base_pos = 'depreciation_base' in wl_acq and \
            wl_acq.index('depreciation_base')
        salvage_value_pos = 'salvage_value' in wl_acq and \
            wl_acq.index('salvage_value')

        acqs = self.assets.filtered(lambda r: r in acquisitions)
        acqs_and_parents = []
        for acq in acqs:
            self._view_add(acq, acqs_and_parents)

        entries = []
        for asset_i, asset in enumerate(acqs_and_parents):
            entry = {}
            if asset.type == 'view':
                cp_i = asset_i + 1
                cp = []
                for a in acqs_and_parents[cp_i:]:
                    if a.parent_id == asset:
                        cp.append(cp_i)
                    cp_i += 1
                entry['child_pos'] = cp
            entry['asset'] = asset
            entries.append(entry)

        for entry in entries:
            asset = entry['asset']
            if asset.type == 'view':
                depreciation_base_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         depreciation_base_pos)
                    for x in entry['child_pos']]
                asset_formula = '+'.join(depreciation_base_cells)
                salvage_value_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         salvage_value_pos)
                    for x in entry['child_pos']]
                salvage_formula = '+'.join(salvage_value_cells)
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset_view',
                    render_space={
                        'asset': asset,
                        'asset_formula': asset_formula,
                        'salvage_formula': salvage_formula,
                    },
                    default_format=self.format_theader_blue_left)
            else:
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset',
                    render_space={'asset': asset},
                    default_format=self.format_tcell_left)

        asset_total_formula = self._rowcol_to_cell(row_pos_start,
                                                   depreciation_base_pos)
        salvage_total_formula = self._rowcol_to_cell(row_pos_start,
                                                     salvage_value_pos)
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'asset_total_formula': asset_total_formula,
                'salvage_total_formula': salvage_total_formula,
            },
            default_format=self.format_theader_yellow_left)

    def _active_report(self, workbook, ws, ws_params, data, wiz):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        wl_act = ws_params['wanted_list']
        if 'account' not in wl_act:
            raise UserError(_(
                "The 'account' field is a mandatory entry of the "
                "'_xls_active_fields' list !"))

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._report_title(ws, row_pos, ws_params, data, wiz)

        if not wiz.date_range_id.type_id.fiscal_year:
            raise UserError(_(
                "The current version of the asset mangement reporting "
                "module supports only fiscal year based reports."
            ))
        fy = wiz.date_range_id
        actives = self.env['account.asset'].search(
            [('date_start', '<=', fy.date_end),
             '|',
             ('date_remove', '=', False),
             ('date_remove', '>=', fy.date_start),
             ('type', '=', 'normal'),
             ('id', 'in', self.assets.ids)],
            order='date_start ASC')

        if not actives:
            return self._empty_report(
                ws, row_pos, ws_params, data, wiz, 'active')

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        row_pos_start = row_pos
        depreciation_base_pos = 'depreciation_base' in wl_act and \
            wl_act.index('depreciation_base')
        salvage_value_pos = 'salvage_value' in wl_act and \
            wl_act.index('salvage_value')
        fy_start_value_pos = 'fy_start_value' in wl_act and \
            wl_act.index('fy_start_value')
        fy_end_value_pos = 'fy_end_value' in wl_act and \
            wl_act.index('fy_end_value')

        acts = self.assets.filtered(lambda r: r in actives)
        acts_and_parents = []
        for act in acts:
            self._view_add(act, acts_and_parents)

        entries = []
        for asset_i, asset in enumerate(acts_and_parents):
            entry = {}

            if asset.type == 'view':
                cp_i = asset_i + 1
                cp = []
                for a in acts_and_parents[cp_i:]:
                    if a.parent_id == asset:
                        cp.append(cp_i)
                    cp_i += 1
                entry['child_pos'] = cp

            else:

                # fy_start_value
                dls = asset.depreciation_line_ids.filtered(
                    lambda r: r.line_date >= fy.date_start
                    and r.type == 'depreciate')
                dls = dls.sorted(key=lambda r: r.line_date)
                if dls:
                    value_depreciated = dls[0].depreciated_value
                elif asset.state in ['close', 'removed']:
                    value_depreciated = asset.value_depreciated
                elif not asset.method_number:
                    value_depreciated = 0.0
                else:
                    error_name = asset.name
                    if asset.code:
                        error_name += ' (' + asset.code + ')' or ''
                    if asset.state in ['open']:
                        dls = asset.depreciation_line_ids.filtered(
                            lambda r: r.line_date < fy.date_start
                            and r.type == 'depreciate'
                            and not r.init_entry
                            and not r.move_check)
                        dls = dls.sorted(key=lambda r: r.line_date)
                        if dls:
                            raise UserError(
                                _("You can not report on a Fiscal Year "
                                  "with unposted entries in prior years. "
                                  "Please post depreciation table entry "
                                  "dd. '%s'  of asset '%s' !")
                                % (dls[0].line_date, error_name))
                        else:
                            raise UserError(
                                _("Depreciation Table error for asset %s !")
                                % error_name)
                    else:
                        raise UserError(
                            _("Depreciation Table error for asset %s !")
                            % error_name)
                asset.fy_start_value = \
                    asset.depreciation_base - value_depreciated

                # fy_end_value
                dls = asset.depreciation_line_ids.filtered(
                    lambda r: r.line_date > fy.date_end
                    and r.type == 'depreciate')
                dls = dls.sorted(key=lambda r: r.line_date)
                if dls:
                    value_depreciated = dls[0].depreciated_value
                elif not asset.method_number:
                    value_depreciated = 0.0
                else:
                    value_depreciated = asset.depreciation_base
                asset.fy_end_value = \
                    asset.depreciation_base - value_depreciated

            entry['asset'] = asset
            entries.append(entry)

        for entry in entries:
            asset = entry['asset']

            fy_start_value_cell = self._rowcol_to_cell(
                row_pos, fy_start_value_pos)
            fy_end_value_cell = self._rowcol_to_cell(
                row_pos, fy_end_value_pos)
            depreciation_base_cell = self._rowcol_to_cell(
                row_pos, depreciation_base_pos)
            fy_diff_formula = fy_start_value_cell + '-' + fy_end_value_cell
            total_depr_formula = depreciation_base_cell \
                + '-' + fy_end_value_cell

            if asset.type == 'view':

                depreciation_base_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         depreciation_base_pos)
                    for x in entry['child_pos']]
                asset_formula = '+'.join(depreciation_base_cells)

                salvage_value_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         salvage_value_pos)
                    for x in entry['child_pos']]
                salvage_formula = '+'.join(salvage_value_cells)

                fy_start_value_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         fy_start_value_pos)
                    for x in entry['child_pos']]
                fy_start_formula = '+'.join(fy_start_value_cells)

                fy_end_value_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         fy_end_value_pos)
                    for x in entry['child_pos']]
                fy_end_formula = '+'.join(fy_end_value_cells)

                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset_view',
                    render_space={
                        'asset': asset,
                        'asset_formula': asset_formula,
                        'salvage_formula': salvage_formula,
                        'fy_start_formula': fy_start_formula,
                        'fy_end_formula': fy_end_formula,
                        'fy_diff_formula': fy_diff_formula,
                        'total_depr_formula': total_depr_formula,
                    },
                    default_format=self.format_theader_blue_left)

            else:
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset',
                    render_space={
                        'asset': asset,
                        'fy_diff_formula': fy_diff_formula,
                        'total_depr_formula': total_depr_formula,
                        },
                    default_format=self.format_tcell_left)

        asset_total_formula = self._rowcol_to_cell(row_pos_start,
                                                   depreciation_base_pos)
        salvage_total_formula = self._rowcol_to_cell(row_pos_start,
                                                     salvage_value_pos)
        fy_start_total_formula = self._rowcol_to_cell(row_pos_start,
                                                      fy_start_value_pos)
        fy_end_total_formula = self._rowcol_to_cell(row_pos_start,
                                                    fy_end_value_pos)
        fy_start_value_cell = self._rowcol_to_cell(row_pos, fy_start_value_pos)
        fy_end_value_cell = self._rowcol_to_cell(row_pos, fy_end_value_pos)
        depreciation_base_cell = self._rowcol_to_cell(row_pos,
                                                      depreciation_base_pos)
        fy_diff_formula = fy_start_value_cell + '-' + fy_end_value_cell
        total_depr_formula = depreciation_base_cell + '-' + fy_end_value_cell

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'asset_total_formula': asset_total_formula,
                'salvage_total_formula': salvage_total_formula,
                'fy_start_total_formula': fy_start_total_formula,
                'fy_end_total_formula': fy_end_total_formula,
                'fy_diff_formula': fy_diff_formula,
                'total_depr_formula': total_depr_formula,
            },
            default_format=self.format_theader_yellow_left)

    def _removal_report(self, workbook, ws, ws_params, data, wiz):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        wl_dsp = ws_params['wanted_list']
        if 'account' not in wl_dsp:
            raise UserError(_(
                "The 'account' field is a mandatory entry of the "
                "'_xls_removal_fields' list !"))

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._report_title(ws, row_pos, ws_params, data, wiz)

        if not wiz.date_range_id.type_id.fiscal_year:
            raise UserError(_(
                "The current version of the asset mangement reporting "
                "module supports only fiscal year based reports."
            ))
        fy = wiz.date_range_id
        removals = self.env['account.asset'].search(
            [('date_remove', '>=', fy.date_start),
             ('date_remove', '<=', fy.date_end),
             ('type', '=', 'normal'),
             ('id', 'in', self.assets.ids)],
            order='date_remove ASC')

        if not removals:
            return self._empty_report(
                ws, row_pos, ws_params, data, wiz, 'removal')

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        row_pos_start = row_pos
        depreciation_base_pos = 'depreciation_base' in wl_dsp and \
            wl_dsp.index('depreciation_base')
        salvage_value_pos = 'salvage_value' in wl_dsp and \
            wl_dsp.index('salvage_value')

        dsps = self.assets.filtered(lambda r: r in removals)
        dsps_and_parents = []
        for dsp in dsps:
            self._view_add(dsp, dsps_and_parents)

        entries = []
        for asset_i, asset in enumerate(dsps_and_parents):
            entry = {}
            if asset.type == 'view':
                cp_i = asset_i + 1
                cp = []
                for a in dsps_and_parents[cp_i:]:
                    if a.parent_id == asset:
                        cp.append(cp_i)
                    cp_i += 1
                entry['child_pos'] = cp
            entry['asset'] = asset
            entries.append(entry)

        for entry in entries:
            asset = entry['asset']
            if asset.type == 'view':
                depreciation_base_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         depreciation_base_pos)
                    for x in entry['child_pos']]
                asset_formula = '+'.join(depreciation_base_cells)
                salvage_value_cells = [
                    self._rowcol_to_cell(row_pos_start + x,
                                         salvage_value_pos)
                    for x in entry['child_pos']]
                salvage_formula = '+'.join(salvage_value_cells)
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset_view',
                    render_space={
                        'asset': asset,
                        'asset_formula': asset_formula,
                        'salvage_formula': salvage_formula,
                    },
                    default_format=self.format_theader_blue_left)
            else:
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset',
                    render_space={
                        'asset': asset,
                        },
                    default_format=self.format_tcell_left)

        asset_total_formula = self._rowcol_to_cell(row_pos_start,
                                                   depreciation_base_pos)
        salvage_total_formula = self._rowcol_to_cell(row_pos_start,
                                                     salvage_value_pos)

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'asset_total_formula': asset_total_formula,
                'salvage_total_formula': salvage_total_formula,
            },
            default_format=self.format_theader_yellow_left)


AssetReportXlsx(
    'report.account.asset.xlsx',
    'wiz.account.asset.report',
    parser=report_sxw.rml_parse)
