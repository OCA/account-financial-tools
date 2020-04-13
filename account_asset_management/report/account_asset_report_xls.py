# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.translate import translate

_logger = logging.getLogger(__name__)


IR_TRANSLATION_NAME = 'account.asset.report'


class AssetReportXlsx(models.AbstractModel):
    _name = 'report.account_asset_management.asset_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, wb, data, wiz):
        self._grouped_assets = self._get_assets(wiz)
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
                'asset_group': {
                    'type': 'string',
                    'value': self._render("group.name or ''"),
                },
                'asset': {
                    'type': 'string',
                    'value': self._render("asset.name"),
                },
                'width': 40,
            },
            'code': {
                'header': {
                    'type': 'string',
                    'value': self._('Reference'),
                },
                'asset_group': {
                    'type': 'string',
                    'value': self._render("group.code or ''"),
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
                'asset': {
                    'value': self._render("asset.date_start"),
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
                    'value': self._render("asset.date_remove"),
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
                'asset_group': {
                    'type': 'number',
                    'value': self._render("group._depreciation_base"),
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
                'asset_group': {
                    'type': 'number',
                    'value': self._render("group._salvage_value"),
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
            'period_start_value': {
                'header': {
                    'type': 'string',
                    'value': self._('Period Start Value'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_group': {
                    'type': 'number',
                    'value': self._render("group._period_start_value"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'number',
                    'value': self._render("asset._period_start_value"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('period_start_total_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'period_depr': {
                'header': {
                    'type': 'string',
                    'value': self._('Period Depreciation'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_group': {
                    'type': 'formula',
                    'value': self._render("period_diff_formula"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'formula',
                    'value': self._render("period_diff_formula"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('period_diff_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'period_end_value': {
                'header': {
                    'type': 'string',
                    'value': self._('Period End Value'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_group': {
                    'type': 'number',
                    'value': self._render("group._period_end_value"),
                    'format': self.format_theader_blue_amount_right,
                },
                'asset': {
                    'type': 'number',
                    'value': self._render("asset._period_end_value"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('period_end_total_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'period_end_depr': {
                'header': {
                    'type': 'string',
                    'value': self._('Tot. Depreciation'),
                    'format': self.format_theader_yellow_right,
                },
                'asset_group': {
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
            'state': {
                'header': {
                    'type': 'string',
                    'value': self._('Status'),
                    'format': self.format_theader_yellow_center,
                },
                'asset': {
                    'type': 'string',
                    'value': self._render("asset.state"),
                    'format': self.format_tcell_center,
                },
                'width': 8,
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
            'generate_ws_method': '_asset_report',
            'title': title,
            'wanted_list': wl_acq,
            'col_specs': acquisition_template,
            'report_type': 'acquisition',
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
            'generate_ws_method': '_asset_report',
            'title': title,
            'wanted_list': wl_act,
            'col_specs': active_template,
            'report_type': 'active',
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
            'generate_ws_method': '_asset_report',
            'title': title,
            'wanted_list': wl_dsp,
            'col_specs': removal_template,
            'report_type': 'removal',
        }

    def _get_title(self, wiz, report, format='normal'):

        prefix = '{} - {}'.format(wiz.date_from, wiz.date_to)
        if report == 'acquisition':
            if format == 'normal':
                title = prefix + ' : ' + _('New Acquisitions')
            else:
                title = 'ACQ'
        elif report == 'active':
            if format == 'normal':
                title = prefix + ' : ' + _('Active Assets')
            else:
                title = 'ACT'
        else:
            if format == 'normal':
                title = prefix + ' : ' + _('Removed Assets')
            else:
                title = 'DSP'
        return title

    def _report_title(self, ws, row_pos, ws_params, data, wiz):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _empty_report(self, ws, row_pos, ws_params, data, wiz):
        report = ws_params['report_type']
        if report == 'acquisition':
            suffix = _('New Acquisitions')
        elif report == 'active':
            suffix = _('Active Assets')
        else:
            suffix = _('Removed Assets')
        no_entries = _("No") + " " + suffix
        ws.write_string(row_pos, 0, no_entries, self.format_left_bold)

    def _get_assets(self, wiz):

        dom = [('date_start', '<=', wiz.date_to),
               '|',
               ('date_remove', '=', False),
               ('date_remove', '>=', wiz.date_from)]

        parent_group = wiz.asset_group_id
        if parent_group:

            def _child_get(parent):
                groups = [parent]
                children = parent.child_ids
                children = children.sorted(lambda r: r.code or r.name)
                for child in children:
                    if child in groups:
                        raise UserError(_(
                            "Inconsistent reporting structure."
                            "\nPlease correct Asset Group '%s' (id %s)"
                        ) % (child.name, child.id))
                    groups.extend(_child_get(child))
                return groups

            groups = _child_get(parent_group)
            dom.append(('group_ids', 'in', [x.id for x in groups]))

        if not wiz.draft:
            dom.append(('state', '!=', 'draft'))
        self._assets = self.env['account.asset'].search(dom)
        grouped_assets = {}
        self._group_assets(self._assets, parent_group, grouped_assets)
        return grouped_assets

    @staticmethod
    def acquisition_filter(wiz, asset):
        return asset.date_start >= wiz.date_from

    @staticmethod
    def active_filter(wiz, asset):
        return True

    @staticmethod
    def removal_filter(wiz, asset):
        return (
            asset.date_remove and asset.date_remove >= wiz.date_from
            and asset.date_remove <= wiz.date_to)

    def _group_assets(self, assets, group, grouped_assets):
        if group:
            group_assets = assets.filtered(lambda r: group in r.group_ids)
        else:
            group_assets = assets
        group_assets = group_assets.sorted(
            lambda r: (r.date_start or '', r.code))
        grouped_assets[group] = {'assets': group_assets}
        for child in group.child_ids:
            self._group_assets(assets, child, grouped_assets[group])

    def _create_report_entries(self, ws_params, wiz, entries,
                               group, group_val, error_dict):
        report = ws_params['report_type']

        def asset_filter(asset):
            filter = getattr(self, '{}_filter'.format(report))
            return filter(wiz, asset)

        def _has_assets(group, group_val):
            assets = group_val.get('assets')
            assets = assets.filtered(asset_filter)
            if assets:
                return True
            for child in group.child_ids:
                if _has_assets(child, group_val[child]):
                    return True
            return False

        assets = group_val.get('assets')
        assets = assets.filtered(asset_filter)

        # remove empty entries
        if not _has_assets(group, group_val):
            return

        asset_entries = []
        group._depreciation_base = 0.0
        group._salvage_value = 0.0
        group._period_start_value = 0.0
        group._period_end_value = 0.0
        for asset in assets:
            group._depreciation_base += asset.depreciation_base
            group._salvage_value += asset.salvage_value
            dls_all = asset.depreciation_line_ids.filtered(
                lambda r: r.type == 'depreciate')
            dls_all = dls_all.sorted(key=lambda r: r.line_date)
            if not dls_all:
                error_dict['no_table'] += asset
            # period_start_value
            dls = dls_all.filtered(lambda r: r.line_date <= wiz.date_from)
            if dls:
                value_depreciated = dls[-1].depreciated_value + dls[-1].amount
            else:
                value_depreciated = 0.0
            asset._period_start_value = \
                asset.depreciation_base - value_depreciated
            group._period_start_value += asset._period_start_value
            # period_end_value
            dls = dls_all.filtered(lambda r: r.line_date <= wiz.date_to)
            if dls:
                value_depreciated = dls[-1].depreciated_value + dls[-1].amount
            else:
                value_depreciated = 0.0
            asset._period_end_value = \
                asset.depreciation_base - value_depreciated
            group._period_end_value += asset._period_end_value

            asset_entries.append({'asset': asset})

        todos = []
        for g in group.child_ids:
            if _has_assets(g, group_val[g]):
                todos.append(g)

        entries.append({'group': group})
        entries.extend(asset_entries)
        for todo in todos:
            self._create_report_entries(ws_params, wiz, entries,
                                        todo, group_val[todo], error_dict)

    def _asset_report(self, workbook, ws, ws_params, data, wiz):
        report = ws_params['report_type']

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        wl = ws_params['wanted_list']
        if 'account' not in wl:
            raise UserError(_(
                "The 'account' field is a mandatory entry of the "
                "'_xls_%s_fields' list !"
            ) % report)

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._report_title(ws, row_pos, ws_params, data, wiz)

        def asset_filter(asset):
            filter = getattr(self, '{}_filter'.format(report))
            return filter(wiz, asset)

        assets = self._assets.filtered(asset_filter)

        if not assets:
            return self._empty_report(
                ws, row_pos, ws_params, data, wiz)

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        row_pos_start = row_pos
        depreciation_base_pos = 'depreciation_base' in wl and \
            wl.index('depreciation_base')
        salvage_value_pos = 'salvage_value' in wl and \
            wl.index('salvage_value')
        period_start_value_pos = 'period_start_value' in wl and \
            wl.index('period_start_value')
        period_end_value_pos = 'period_end_value' in wl and \
            wl.index('period_end_value')

        entries = []
        root = wiz.asset_group_id
        root_val = self._grouped_assets[root]
        error_dict = {
            'no_table': self.env['account.asset'],
            'dups': self.env['account.asset'],
        }

        self._create_report_entries(ws_params, wiz, entries,
                                    root, root_val, error_dict)

        # traverse entries in reverse order to calc totals
        for i, entry in enumerate(reversed(entries)):
            group = entry.get('group')
            if 'group' in entry:
                parent = group.parent_id
                for e in reversed(entries[:-i-1]):
                    g = e.get('group')
                    if g == parent:
                        g._depreciation_base += group._depreciation_base
                        g._salvage_value += group._salvage_value
                        g._period_start_value += group._period_start_value
                        g._period_end_value += group._period_end_value
                        continue

        processed = []
        for entry in entries:

            period_start_value_cell = period_start_value_pos \
                and self._rowcol_to_cell(row_pos, period_start_value_pos)
            period_end_value_cell = period_end_value_pos \
                and self._rowcol_to_cell(row_pos, period_end_value_pos)
            depreciation_base_cell = depreciation_base_pos \
                and self._rowcol_to_cell(row_pos, depreciation_base_pos)
            period_diff_formula = period_end_value_cell and (
                period_start_value_cell + '-' + period_end_value_cell)
            total_depr_formula = period_end_value_cell and (
                depreciation_base_cell + '-' + period_end_value_cell)

            if 'group' in entry:
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset_group',
                    render_space={
                        'group': entry['group'],
                        'period_diff_formula': period_diff_formula,
                        'total_depr_formula': total_depr_formula,
                    },
                    default_format=self.format_theader_blue_left)

            else:
                asset = entry['asset']
                if asset in processed:
                    error_dict['dups'] += asset
                    continue
                else:
                    processed.append(asset)
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='asset',
                    render_space={
                        'asset': asset,
                        'period_diff_formula': period_diff_formula,
                        'total_depr_formula': total_depr_formula,
                        },
                    default_format=self.format_tcell_left)

        asset_total_formula = depreciation_base_pos \
            and self._rowcol_to_cell(row_pos_start, depreciation_base_pos)
        salvage_total_formula = salvage_value_pos \
            and self._rowcol_to_cell(row_pos_start, salvage_value_pos)
        period_start_total_formula = period_start_value_pos \
            and self._rowcol_to_cell(row_pos_start, period_start_value_pos)
        period_end_total_formula = period_end_value_pos \
            and self._rowcol_to_cell(row_pos_start, period_end_value_pos)
        period_start_value_cell = period_start_value_pos \
            and self._rowcol_to_cell(row_pos, period_start_value_pos)
        period_end_value_cell = period_end_value_pos \
            and self._rowcol_to_cell(row_pos, period_end_value_pos)
        depreciation_base_cell = depreciation_base_pos \
            and self._rowcol_to_cell(row_pos, depreciation_base_pos)
        period_diff_formula = period_end_value_cell and (
            period_start_value_cell + '-' + period_end_value_cell)
        total_depr_formula = period_end_value_cell and (
            depreciation_base_cell + '-' + period_end_value_cell)

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'asset_total_formula': asset_total_formula,
                'salvage_total_formula': salvage_total_formula,
                'period_start_total_formula': period_start_total_formula,
                'period_end_total_formula': period_end_total_formula,
                'period_diff_formula': period_diff_formula,
                'total_depr_formula': total_depr_formula,
            },
            default_format=self.format_theader_yellow_left)

        for k in error_dict:
            if error_dict[k]:
                if k == 'no_table':
                    reason = _("Missing depreciation table")
                elif k == 'dups':
                    reason = _("Duplicate reporting entries")
                else:
                    reason = _("Undetermined error")
                row_pos += 1
                err_msg = _("Assets to be corrected") + ': '
                err_msg += '%s' % [x[1] for x in error_dict[k].name_get()]
                err_msg += ' - ' + _("Reason") + ': ' + reason
                ws.write_string(row_pos, 0, err_msg, self.format_left_bold)
