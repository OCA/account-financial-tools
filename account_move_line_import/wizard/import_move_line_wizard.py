# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import base64
import csv
import time
from datetime import datetime
from sys import exc_info
from traceback import format_exception

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLineImport(models.TransientModel):
    _name = 'aml.import'
    _description = 'Import account move lines'

    aml_data = fields.Binary(string='File', required=True)
    aml_fname = fields.Char(string='Filename')
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

    @api.model
    def _default_codepage(self):
        return 'Windows-1252'

    @api.one
    @api.depends('aml_data')
    def _compute_lines(self):
        if self.aml_data:
            lines = base64.decodestring(self.aml_data)
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

    @api.onchange('aml_data')
    def _onchange_aml_data(self):
        if self.lines:
            self.csv_separator = self.dialect.delimiter
            if self.csv_separator == ';':
                self.decimal_separator = ','

    @api.onchange('csv_separator')
    def _onchange_csv_separator(self):
        if self.csv_separator and self.aml_data:
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
        """
        Extend this dictionary if you want to add support for
        fields requiring pre-processing before being added to
        the move line values dict.
        """
        res = {
            'account': {'method': self._handle_account},
            'account_id': {'required': True},
            'debit': {'method': self._handle_debit, 'required': True},
            'credit': {'method': self._handle_credit, 'required': True},
            'partner': {'method': self._handle_partner},
            'product': {'method': self._handle_product},
            'date_maturity': {'method': self._handle_date_maturity},
            'due date': {'method': self._handle_date_maturity},
            'currency': {'method': self._handle_currency},
            'tax account': {'method': self._handle_tax_code},
            'tax_code': {'method': self._handle_tax_code},
            'analytic account': {'method': self._handle_analytic_account},
        }
        return res

    def _get_orm_fields(self):
        aml_mod = self.env['account.move.line']
        orm_fields = aml_mod.fields_get()
        blacklist = models.MAGIC_COLUMNS + [aml_mod.CONCURRENCY_CHECK_FIELD]
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

            if hf in self._field_methods:
                continue

            if hf not in self._orm_fields \
                    and hf not in [self._orm_fields[f]['string'].lower()
                                   for f in self._orm_fields]:
                _logger.error(
                    _("%s, undefined field '%s' found "
                      "while importing move lines"),
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

    def _handle_orm_char(self, field, line, move, aml_vals,
                         orm_field=False):
        orm_field = orm_field or field
        if not aml_vals.get(orm_field):
            aml_vals[orm_field] = line[field]

    def _handle_orm_integer(self, field, line, move, aml_vals,
                            orm_field=False):
        orm_field = orm_field or field
        if not aml_vals.get(orm_field):
            val = str2int(
                line[field], self.decimal_separator)
            if val is False:
                msg = _(
                    "Incorrect value '%s' "
                    "for field '%s' of type Integer !"
                    ) % (line[field], field)
                self._log_line_error(line, msg)
            else:
                aml_vals[orm_field] = val

    def _handle_orm_float(self, field, line, move, aml_vals,
                          orm_field=False):
        orm_field = orm_field or field
        if not aml_vals.get(orm_field):
            aml_vals[orm_field] = str2float(
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
                aml_vals[orm_field] = val

    def _handle_orm_boolean(self, field, line, move, aml_vals,
                            orm_field=False):
        orm_field = orm_field or field
        if not aml_vals.get(orm_field):
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
                aml_vals[orm_field] = val

    def _handle_orm_many2one(self, field, line, move, aml_vals,
                             orm_field=False):
        orm_field = orm_field or field
        if not aml_vals.get(orm_field):
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
                aml_vals[orm_field] = val

    def _handle_account(self, field, line, move, aml_vals):
        if not aml_vals.get('account_id'):
            code = line[field]
            if code in self._accounts_dict:
                aml_vals['account_id'] = self._accounts_dict[code]
            else:
                msg = _("Account with code '%s' not found !") % code
                self._log_line_error(line, msg)

    def _handle_debit(self, field, line, move, aml_vals):
        if 'debit' not in aml_vals:
            debit = str2float(line[field], self.decimal_separator)
            aml_vals['debit'] = debit
            self._sum_debit += debit

    def _handle_credit(self, field, line, move, aml_vals):
        if 'credit' not in aml_vals:
            credit = str2float(line[field], self.decimal_separator)
            aml_vals['credit'] = credit
            self._sum_credit += credit

    def _handle_partner(self, field, line, move, aml_vals):
        if not aml_vals.get('partner_id'):
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
                aml_vals['partner_id'] = partner.id

    def _handle_product(self, field, line, move, aml_vals):
        if not aml_vals.get('product_id'):
            input = line[field]
            prod_mod = self.env['product.product']
            products = prod_mod.search([
                ('default_code', '=', input)])
            if not products:
                products = prod_mod.search(
                    [('name', '=', input)])
            if not products:
                msg = _("Product '%s' not found !") % input
                self._log_line_error(line, msg)
                return
            elif len(products) > 1:
                msg = _("Multiple products with Internal Reference "
                        "or Name '%s' found !") % input
                self._log_line_error(line, msg)
                return
            else:
                product = products[0]
                aml_vals['product_id'] = product.id

    def _handle_date_maturity(self, field, line, move, aml_vals):
        if not aml_vals.get('date_maturity'):
            due = line[field]
            try:
                datetime.strptime(due, '%Y-%m-%d')
                aml_vals['date_maturity'] = due
            except:
                msg = _("Incorrect data format for field '%s' "
                        "with value '%s', "
                        " should be YYYY-MM-DD") % (field, due)
                self._log_line_error(line, msg)

    def _handle_currency(self, field, line, move, aml_vals):
        if not aml_vals.get('currency_id'):
            name = line[field]
            curr = self.env['res.currency'].search([
                ('name', '=ilike', name)])
            if curr:
                aml_vals['currency_id'] = curr[0].id
            else:
                msg = _("Currency '%s' not found !") % name
                self._log_line_error(line, msg)

    def _handle_tax_code(self, field, line, move, aml_vals):
        if not aml_vals.get('tax_code_id'):
            input = line[field]
            tc_mod = self.env['account.tax.code']
            codes = tc_mod.search([
                ('code', '=', input)])
            if not codes:
                codes = tc_mod.search(
                    [('name', '=', input)])
            if not codes:
                msg = _("%s '%s' not found !") % (field, input)
                self._log_line_error(line, msg)
                return
            elif len(codes) > 1:
                msg = _("Multiple %s entries with Code "
                        "or Name '%s' found !") % (field, input)
                self._log_line_error(line, msg)
                return
            else:
                code = codes[0]
                aml_vals['tax_code_id'] = code.id

    def _handle_analytic_account(self, field, line, move, aml_vals):
        if not aml_vals.get('analytic_account_id'):
            ana_mod = self.env['account.analytic.account']
            input = line[field]
            domain = [('type', '!=', 'view'),
                      ('company_id', '=', move.company_id.id),
                      ('state', 'not in', ['close', 'cancelled'])]
            analytic_accounts = ana_mod.search(
                domain + [('code', '=', input)])
            if len(analytic_accounts) == 1:
                aml_vals['analytic_account_id'] = analytic_accounts.id
            else:
                analytic_accounts = ana_mod.search(
                    domain + [('name', '=', input)])
                if len(analytic_accounts) == 1:
                    aml_vals['analytic_account_id'] = analytic_accounts.id
            if not analytic_accounts:
                msg = _("Invalid Analytic Account '%s' !") % input
                self._log_line_error(line, msg)
            elif len(analytic_accounts) > 1:
                msg = _("Multiple Analytic Accounts found "
                        "that match with '%s' !") % input
                self._log_line_error(line, msg)

    def _process_line_vals(self, line, move, aml_vals):
        """
        Use this method if you want to check/modify the
        line input values dict before calling the move write() method
        """
        if 'name' not in aml_vals:
            aml_vals['name'] = '/'

        if 'debit' not in aml_vals:
            aml_vals['debit'] = 0.0

        if 'credit' not in aml_vals:
            aml_vals['credit'] = 0.0

        if 'partner_id' not in aml_vals:
            # required since otherwise the partner_id
            # of the previous entry is added
            aml_vals['partner_id'] = False

        all_fields = self._field_methods
        required_fields = [x for x in all_fields
                           if all_fields[x].get('required')]
        for rf in required_fields:
            if rf not in aml_vals:
                msg = _("The '%s' field is a required field "
                        "that must be correctly set.") % rf
                self._log_line_error(line, msg)

    def _process_vals(self, move, vals):
        """
        Use this method if you want to check/modify the
        input values dict before calling the move write() method
        """
        dp = self.env['decimal.precision'].precision_get('Account')
        if round(self._sum_debit, dp) != round(self._sum_credit, dp):
            self._err_log += '\n' + _(
                "Error in CSV file, Total Debit (%s) is "
                "different from Total Credit (%s) !"
                ) % (self._sum_debit, self._sum_credit) + '\n'
        return vals

    @api.multi
    def aml_import(self):

        time_start = time.time()
        self._err_log = ''
        move = self.env['account.move'].browse(
            self._context['active_id'])
        accounts = self.env['account.account'].search([
            ('type', 'not in', ['view', 'consolidation', 'closed']),
            ('company_id', '=', move.company_id.id)
            ])
        self._accounts_dict = {a.code: a.id for a in accounts}
        self._sum_debit = self._sum_credit = 0.0
        self._get_orm_fields()
        lines, header = self._remove_leading_lines(self.lines)
        header_fields = csv.reader(
            StringIO.StringIO(header), dialect=self.dialect).next()
        self._header_fields = self._process_header(header_fields)
        reader = csv.DictReader(
            StringIO.StringIO(lines), fieldnames=self._header_fields,
            dialect=self.dialect)

        move_lines = []
        for line in reader:

            aml_vals = {}

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
                        hf, line, move, aml_vals,
                        orm_field=self._field_methods[hf]['orm_field'])
                else:
                    self._field_methods[hf]['method'](
                        hf, line, move, aml_vals)

            if aml_vals:
                self._process_line_vals(line, move, aml_vals)
                move_lines.append(aml_vals)

        vals = [(0, 0, l) for l in move_lines]
        vals = self._process_vals(move, vals)

        if self._err_log:
            self.note = self._err_log
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = self.env.ref(
                '%s.aml_import_view_form_result' % module)
            return {
                'name': _("Import File result"),
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'aml.import',
                'view_id': result_view.id,
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            ctx = dict(self._context, novalidate=True)
            move.with_context(ctx).write({'line_id': vals})
            import_time = time.time() - time_start
            _logger.warn(
                'account.move %s import time = %.3f seconds',
                move.name, import_time)
            return {'type': 'ir.actions.act_window_close'}


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
