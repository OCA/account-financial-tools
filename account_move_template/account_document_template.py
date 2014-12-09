# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 - 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, exceptions, _
import re


class AccountDocumentTemplate(models.Model):
    _name = 'account.document.template'

    name = fields.Char(required=True)

    @api.model
    def _input_lines(self, template):
        count = 0
        for line in template.template_line_ids:
            if line.type == 'input':
                count += 1
        return count

    @api.model
    def _get_template_line(self, template_id, line_number):
        template = self.browse(template_id)
        for line in template.template_line_ids:
            if line.sequence == line_number:
                return line
        return False

    @api.model
    def _generate_empty_lines(self, template_id):
        lines = {}
        template = self.browse(template_id)
        for line in template.template_line_ids:
            lines[line.sequence] = None
        return lines

    @api.model
    def lines(self, line_number):
        if self._computed_lines[line_number] is not None:
            return self._computed_lines[line_number]
        line = self._get_template_line(self._current_template_id, line_number)
        if re.match(r'L\( *' + str(line_number) + r' *\)', line.python_code):
            raise exceptions.Warning(
                _('Error'),
                _('Line %s can\'t refer to itself') % str(line_number)
            )
        try:
            self._computed_lines[line_number] = eval(
                line.python_code.replace('L', 'self.lines')
            )
        except KeyError:
            raise exceptions.Warning(
                _('Error'),
                _('Code "%s" refers to non existing line') % line.python_code)
        return self._computed_lines[line_number]

    @api.model
    def compute_lines(self, template_id, input_lines):
        # input_lines: dictionary in the form {line_number: line_amount}
        # returns all the lines (included input lines)
        # in the form {line_number: line_amount}
        template = self.browse(template_id)
        if len(input_lines) != self._input_lines(template):
            raise exceptions.Warning(
                _('Error'),
                _('Inconsistency between input lines and '
                  'filled lines for template %s') % template.name
            )
        self._current_template_id = template.id
        self._computed_lines = self._generate_empty_lines(template_id)
        self._computed_lines.update(input_lines)
        for line_number in self._computed_lines:
            self.lines(line_number)
        return self._computed_lines

    @api.model
    def check_zero_lines(self, wizard):
        if not wizard.line_ids:
            return True
        for template_line in wizard.line_ids:
            if template_line.amount:
                return True
        return False


class AccountDocumentTemplateLine(models.Model):
    _name = 'account.document.template.line'

    name = fields.Char(required=True)
    sequence = fields.Integer(string='Sequence', required=True)
    type = fields.Selection(
        [('computed', 'Computed'), ('input', 'User input')],
        string='Type',
        required=True
    )
    python_code = fields.Text(string='Python Code')
