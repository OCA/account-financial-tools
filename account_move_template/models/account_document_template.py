# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, exceptions, _
from odoo.tools.safe_eval import safe_eval
from functools import partial
import re


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
    def lines(self, line_number, computed_lines=None):
        if computed_lines is None:
            computed_lines = {}
        if computed_lines[line_number] is not None:
            return computed_lines[line_number]
        line = self._get_template_line(line_number)
        if re.match(r'L\( *' + str(line_number) + r' *\)', line.python_code):
            raise exceptions.Warning(
                _('Line %s can\'t refer to itself') % str(line_number)
            )
        try:
            recurse_lines = partial(self.lines, computed_lines=computed_lines)
            computed_lines[line_number] = safe_eval(
                line.python_code.replace('L', 'recurse_lines'),
                locals_dict={'recurse_lines': recurse_lines}
            )
        except KeyError:
            raise exceptions.Warning(
                _('Code "%s" refers to non existing line') % line.python_code)
        return computed_lines[line_number]

    @api.multi
    def compute_lines(self, input_lines):
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
                line_number, computed_lines)
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
