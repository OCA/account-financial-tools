# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, exceptions, _
from odoo.tools.safe_eval import safe_eval
from functools import partial
import re

import logging
_logger = logging.getLogger(__name__)


class AccountDocumentTemplate(models.Model):
    _name = 'account.document.template'

    name = fields.Char(required=True)

    @api.multi
    def _input_lines(self):
        count = 0
        for line in self.template_line_ids:
            if line.type == 'input':
                count += 1
        return count

    @api.multi
    def _get_template_line(self, line_number):
        for line in self.template_line_ids:
            if line.sequence == line_number:
                return line
        return False

    @api.multi
    def _generate_empty_lines(self):
        lines = {}
        for line in self.template_line_ids:
            lines[line.sequence] = None
        return lines

    @api.multi
    def lines(self, line_number, date_from=None, date_to=None, computed_lines=None, partner_id=False):
        def replace_all(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        if computed_lines is None:
            computed_lines = {}
        if computed_lines[line_number] is not None:
            return computed_lines[line_number]
        line = self._get_template_line(line_number)
        if re.match(r'L\( *' + str(line_number) + r' *\)', line.python_code):
            raise exceptions.Warning(
                _('Line %s can\'t refer to itself') % str(line_number)
            )
        if date_from:
            fy = {'date_from': date_from, 'date_to': date_to}
        else:
            fy = line.template_id.company_id.compute_fiscalyear_dates(date_to)
        domain = [('account_id', '=', line.account_id.id)]
        if line.analytic_account_id:
            domain += [('analytic_account_id', '=', line.analytic_account_id.id)]
        if partner_id:
            domain += [('partner_id', '=', partner_id)]
        move = self.env['account.move.line'].search(domain)
        domain += [('date_maturity', '>=', fields.Date.to_string(fy['date_from'])), ('date_maturity', '<=', fields.Date.to_string(fy['date_to']))]
        move_fy = self.env['account.move.line'].search(domain)
        #recurse_lines = partial(self.lines, computed_lines=computed_lines)
        account_debit = sum([x.debit for x in move])
        account_credit = sum([x.credit for x in move])
        account_debit_fy = sum([x.debit for x in move_fy])
        account_credit_fy = sum([x.credit for x in move_fy])

        try:
            recurse_lines = partial(self.lines, date_from=date_from, date_to=date_to, computed_lines=computed_lines, partner_id=partner_id)
            local_dict = {
                        'recurse_lines': recurse_lines,
                        'account_debit': account_debit,
                        'account_credit': account_credit,
                        'account_debit_fy': account_debit_fy,
                        'account_credit_fy': account_credit_fy,
                        'account_saldo_fy': account_debit_fy-account_credit_fy,
                    }
            python_code = replace_all(line.python_code, {
                                                    'DBTFY': 'account_debit_fy',
                                                    'CRTFY': 'account_credit_fy',
                                                    'SALFY': 'account_saldo_fy',
                                                    'DBT': 'account_debit',
                                                    'CRT': 'account_credit',
                                                    'SAL': '(account_debit - account_credit)',
                                                    'L': 'recurse_lines',
                                                    }).rstrip()
            #_logger.info("code: %s:%s:%s" % (python_code,local_dict,recurse_lines))
            computed_lines[line_number] = safe_eval(python_code, locals_dict=local_dict)
        except KeyError:
            raise exceptions.Warning(
                _('Code "%s" refers to non existing line') % line.python_code)
        return computed_lines[line_number]

    @api.multi
    def compute_lines(self, input_lines, date_from, date_to, partner_id=False):
        if len(input_lines) != self._input_lines():
            raise exceptions.Warning(
                _('You can not add a different number of lines in this wizard '
                  'you should try to create the move normally and then edit '
                  'the created move. Inconsistent between input lines and '
                  ' filled lines for template %s') % self.name
            )
        computed_lines = self._generate_empty_lines()
        computed_lines.update(input_lines)
        for line_number in computed_lines:
            computed_lines[line_number] = self.lines(
                line_number, date_from, date_to, computed_lines, partner_id=partner_id)
        return computed_lines


class AccountDocumentTemplateLine(models.Model):
    _name = 'account.document.template.line'

    name = fields.Char(required=True)
    sequence = fields.Integer(required=True)
    type = fields.Selection([
        ('computed', 'Computed'),
        ('input', 'User input'),
    ], required=True, default='input')
    python_code = fields.Text()
