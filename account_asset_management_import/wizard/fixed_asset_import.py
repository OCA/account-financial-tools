# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import base64
import csv
import time
from sys import exc_info
from traceback import format_exception

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class FixedAssetImport(models.TransientModel):
    _name = 'fixed.asset.import'

    fa_data = fields.Binary(string='File', required=True)
    fa_fname = fields.Char(string='Filename')
    lines = fields.Binary(
        compute='_compute_lines', string='Input Lines', required=True)
    dialect = fields.Binary(
        compute='_compute_dialect', string='Dialect', required=True)
    csv_separator = fields.Selection(
        [(',', ', (comma)'), (';', '; (semicolon)')],
        string='CSV Separator', required=True)
    decimal_separator = fields.Selection(
        [('.', '. (dot)'), (',', ', (comma)')],
        string='Decimal Separator',
        default='.', required=True)
    codepage = fields.Char(
        string='Code Page',
        default=lambda self: self._default_codepage(),
        help="Code Page of the system that has generated the csv file."
             "\nE.g. Windows-1252, utf-8")
    note = fields.Text('Log')
    compute_board = fields.Boolean(
        string='Compute Depreciation Board',
        help="Select this option if you want to compute "
             "the depreciation tables for the new created assets."
             "\nThis option may take a considerable amount of time "
             "when importing a large number of assets.")

    @api.model
    def _default_codepage(self):
        return 'Windows-1252'

    @api.one
    @api.depends('fa_data')
    def _compute_lines(self):
        if self.fa_data:
            lines = base64.decodestring(self.fa_data)
            # convert windows & mac line endings to unix style
            self.lines = lines.replace('\r\n', '\n').replace('\r', '\n')

    @api.one
    @api.depends('lines', 'csv_separator')
    def _compute_dialect(self):
        if self.lines:
            try:
                self.dialect = csv.Sniffer().sniff(
                    self.lines[:128], delimiters=';,')
            except:
                # csv.Sniffer is not always reliable
                # in the detection of the delimiter
                self.dialect = csv.Sniffer().sniff(
                    '"header 1";"header 2";\r\n')
                if ',' in self.lines[128]:
                    self.dialect.delimiter = ','
                elif ';' in self.lines[128]:
                    self.dialect.delimiter = ';'
        if self.csv_separator:
            self.dialect.delimiter = str(self.csv_separator)

    @api.onchange('fa_data')
    def _onchange_fa_data(self):
        if self.lines:
            self.csv_separator = self.dialect.delimiter
            if self.csv_separator == ';':
                self.decimal_separator = ','

    @api.onchange('csv_separator')
    def _onchange_csv_separator(self):
        if self.csv_separator and self.fa_data:
            self.dialect.delimiter = self.csv_separator

    def _remove_leading_lines(self, lines):
        """ remove leading blank or comment lines """
        input = StringIO.StringIO(lines)
        header = False
        while not header:
            ln = input.next()
            if not ln or ln and ln[0] in [self.csv_separator, '#']:
                continue
            else:
                header = ln.lower()
        if not header:
            raise UserError(
                _("No header line found in the input file !"))
        output = input.read()
        return output, header

    def _input_fields(self):
        res = {
            'reference': {'method': self._handle_reference},
            'partner': {'method': self._handle_partner},
            'asset profile': {'method': self._handle_profile},
        }
        return res

    def _get_orm_fields(self):
        fa_mod = self.env['account.asset']
        orm_fields = fa_mod.fields_get()
        blacklist = models.MAGIC_COLUMNS + [fa_mod.CONCURRENCY_CHECK_FIELD]
        self._orm_fields = {
            f: orm_fields[f] for f in orm_fields
            if f not in blacklist and not orm_fields[f].get('depends')}

    def _process_header(self, header_fields):

        self._field_methods = self._input_fields()
        self._skip_fields = []

        # header fields after blank column are considered as comments
        column_cnt = 0
        for cnt in range(len(header_fields)):
            if header_fields[cnt] == '':
                column_cnt = cnt
                break
            elif cnt == len(header_fields) - 1:
                column_cnt = cnt + 1
                break
        header_fields = header_fields[:column_cnt]

        # check for duplicate header fields
        header_fields2 = []
        for hf in header_fields:
            if hf in header_fields2:
                raise UserError(_(
                    "Duplicate header field '%s' found !"
                    "\nPlease correct the input file.")
                    % hf)
            else:
                header_fields2.append(hf)

        for i, hf in enumerate(header_fields):

            if hf in self._field_methods \
                    and self._field_methods[hf].get('method'):
                continue

            if hf not in self._orm_fields \
                    and hf not in [self._orm_fields[f]['string'].lower()
                                   for f in self._orm_fields]:
                _logger.error(
                    _("%s, undefined field '%s' found "
                      "while importing assets"),
                    self._name, hf)
                self._skip_fields.append(hf)
                continue

            field_def = self._orm_fields.get(hf)
            if not field_def:
                for f in self._orm_fields:
                    if self._orm_fields[f]['string'].lower() == hf:
                        orm_field = f
                        field_def = self._orm_fields.get(f)
                        break
            else:
                orm_field = hf
            field_type = field_def['type']

            try:
                ft = field_type == 'text' and 'char' or field_type
                self._field_methods[hf] = {
                    'method': getattr(self, '_handle_orm_%s' % ft),
                    'orm_field': orm_field,
                }
            except AttributeError:
                _logger.error(
                    _("%s, field '%s', "
                      "the import of ORM fields of type '%s' "
                      "is not supported"),
                    self._name, hf, field_type)
                self._skip_fields.append(hf)

        return header_fields

    def _log_line_error(self, line, msg):
        data = self.csv_separator.join(
            [line[hf] for hf in self._header_fields])
        self._err_log += _(
            "Error when processing line '%s'") % data + ':\n' + msg + '\n\n'

    def _handle_orm_char(self, field, line, fa_vals,
                         orm_field=False):
        orm_field = orm_field or field
        fa_vals[orm_field] = line[field]

    def _handle_orm_date(self, field, line, fa_vals,
                         orm_field=False):
        orm_field = orm_field or field
        fa_vals[orm_field] = line[field]

    def _handle_orm_selection(self, field, line, fa_vals,
                              orm_field=False):
        orm_field = orm_field or field
        fa_vals[orm_field] = line[field]

    def _handle_orm_integer(self, field, line, fa_vals,
                            orm_field=False):
        orm_field = orm_field or field
        val = str2int(
            line[field], self.decimal_separator)
        if val is False:
            msg = _(
                "Incorrect value '%s' "
                "for field '%s' of type Integer !"
            ) % (line[field], field)
            self._log_line_error(line, msg)
        else:
            fa_vals[orm_field] = val

    def _handle_orm_float(self, field, line, fa_vals,
                          orm_field=False):
        orm_field = orm_field or field
        fa_vals[orm_field] = str2float(
            line[field], self.decimal_separator)

        val = str2float(
            line[field], self.decimal_separator)
        if val is False:
            msg = _(
                "Incorrect value '%s' "
                "for field '%s' of type Numeric !"
            ) % (line[field], field)
            self._log_line_error(line, msg)
        else:
            fa_vals[orm_field] = val

    def _handle_orm_boolean(self, field, line, fa_vals,
                            orm_field=False):
        orm_field = orm_field or field
        val = line[field].capitalize()
        if val in ['', '0', 'False']:
            val = False
        elif val in ['1', 'True']:
            val = True
        if isinstance(val, basestring):
            msg = _(
                "Incorrect value '%s' "
                "for field '%s' of type Boolean !"
            ) % (line[field], field)
            self._log_line_error(line, msg)
        else:
            fa_vals[orm_field] = val

    def _handle_orm_many2one(self, field, line, fa_vals,
                             orm_field=False):
        orm_field = orm_field or field
        val = str2int(
            line[field], self.decimal_separator)
        if val is False:
            msg = _(
                "Incorrect value '%s' "
                "for field '%s' of type Many2One !"
                "\nYou should specify the database key "
                "or contact your IT department "
                "to add support for this field."
            ) % (line[field], field)
            self._log_line_error(line, msg)
        else:
            fa_vals[orm_field] = val

    def _handle_reference(self, field, line, fa_vals):
        code = line[field]
        if code:
            dups = self.env['account.asset'].search([('code', '=', code)])
            if dups:
                msg = _("Duplicate Asset with reference '%s' found !") % code
                self._log_line_error(line, msg)
                return
            fa_vals['code'] = code

    def _handle_partner(self, field, line, fa_vals):
        if not fa_vals.get('partner_id'):
            input = line[field]
            part_mod = self.env['res.partner']
            dom = ['|', ('parent_id', '=', False), ('is_company', '=', True)]
            dom_ref = dom + [('ref', '=', input)]
            partners = part_mod.search(dom_ref)
            if not partners:
                dom_name = dom + [('name', '=', input)]
                partners = part_mod.search(dom_name)
            if not partners:
                msg = _("Partner '%s' not found !") % input
                self._log_line_error(line, msg)
                return
            elif len(partners) > 1:
                msg = _("Multiple partners with Reference "
                        "or Name '%s' found !") % input
                self._log_line_error(line, msg)
                return
            else:
                partner = partners[0]
                fa_vals['partner_id'] = partner.id

    def _handle_profile(self, field, line, fa_vals):
        if not fa_vals.get('profile_id'):
            input = line[field]
            profile = self.env['account.asset.profile'].search([
                ('name', '=', input)])
            if not profile:
                msg = _("Profile '%s' not found !") % input
                self._log_line_error(line, msg)
                return
            elif len(profile) > 1:
                msg = _("Multiple profiles with Internal Reference "
                        "or Name '%s' found !") % input
                self._log_line_error(line, msg)
                return
            else:
                fa_vals['profile_id'] = profile.id
        self._play_onchange_profile_id(fa_vals)

    def _process_fa_vals(self, line, fa_vals):
        """
        Use this method if you want to check/modify the
        input values dict before calling the create() method
        """
        all_fields = self._field_methods
        required_fields = [x for x in all_fields
                           if all_fields[x].get('required')]
        for rf in required_fields:
            if rf not in fa_vals:
                msg = _("The '%s' field is a required field "
                        "that must be correctly set.") % rf
                self._log_line_error(line, msg)

    @api.model
    def _play_onchange_profile_id(self, vals):
        asset_obj = self.env['account.asset']
        asset_temp = asset_obj.new(vals)
        asset_temp._onchange_profile_id()
        for field in asset_temp._fields:
            if field not in vals and asset_temp[field]:
                vals[field] = asset_temp._fields[field].\
                    convert_to_write(asset_temp[field], asset_temp)

    @api.multi
    def fa_import(self):

        time_start = time.time()
        self._err_log = ''
        self._get_orm_fields()
        lines, header = self._remove_leading_lines(self.lines)
        header_fields = csv.reader(
            StringIO.StringIO(header), dialect=self.dialect).next()
        self._header_fields = self._process_header(header_fields)
        reader = csv.DictReader(
            StringIO.StringIO(lines), fieldnames=self._header_fields,
            dialect=self.dialect)

        fa_vals_list = []
        for line in reader:

            fa_vals = {}

            # step 1: handle codepage
            for i, hf in enumerate(self._header_fields):
                try:
                    line[hf] = line[hf].decode(self.codepage).strip()
                except:
                    tb = ''.join(format_exception(*exc_info()))
                    raise UserError(
                        _("Wrong Code Page"),
                        _("Error while processing line '%s' :\n%s")
                        % (line, tb))

            # step 2: process input fields
            for i, hf in enumerate(self._header_fields):
                if i == 0 and line[hf] and line[hf][0] == '#':
                    # lines starting with # are considered as comment lines
                    break
                if hf in self._skip_fields:
                    continue
                if line[hf] == '':
                    continue

                if self._field_methods[hf].get('orm_field'):
                    self._field_methods[hf]['method'](
                        hf, line, fa_vals,
                        orm_field=self._field_methods[hf]['orm_field'])
                else:
                    self._field_methods[hf]['method'](
                        hf, line, fa_vals)

            if fa_vals:
                self._process_fa_vals(line, fa_vals)
                fa_vals_list.append(fa_vals)

        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.%s_view_form_result' % (module, self._table))

        ctx = self._context.copy()
        if self._err_log:
            self.note = self._err_log
        else:
            new_assets = self.env['account.asset']
            for fa_vals in fa_vals_list:
                fa = self.env['account.asset'].create(fa_vals)
                new_assets += fa
            if self.compute_board:
                new_assets.compute_depreciation_board()
            import_time = time.time() - time_start
            self.note = (
                "%s assets have been created."
                % len(new_assets))
            ctx['new_asset_ids'] = new_assets.ids
            _logger.warn(
                "%s assets have been created, "
                "import time = %.3f seconds.",
                len(new_assets), import_time)
        return {
            'name': _("Import result"),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'view_id': result_view.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

    @api.multi
    def view_assets(self):
        self.ensure_one()
        domain = [('id', 'in', self._context.get('new_asset_ids', []))]
        return {
            'name': _('Imported Assets'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset',
            'view_id': False,
            'domain': domain,
            'type': 'ir.actions.act_window',
        }


def str2float(amount, decimal_separator):
    if not amount:
        return 0.0
    try:
        if decimal_separator == '.':
            return float(amount.replace(',', ''))
        else:
            return float(amount.replace('.', '').replace(',', '.'))
    except:
        return False


def str2int(amount, decimal_separator):
    if not amount:
        return 0
    try:
        if decimal_separator == '.':
            return int(amount.replace(',', ''))
        else:
            return int(amount.replace('.', '').replace(',', '.'))
    except:
        return False
