# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
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
import time


class WizardSelectMoveTemplate(models.TransientModel):
    _name = "wizard.select.move.template"

    template_id = fields.Many2one(
        comodel_name='account.move.template',
        string='Move Template',
        required=True
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner'
    )
    line_ids = fields.One2many(
        comodel_name='wizard.select.move.template.line',
        inverse_name='template_id',
        string='Lines'
    )
    state = fields.Selection(
        [('template_selected', 'Template selected')],
        string='State'
    )

    @api.multi
    def check_zero_lines(self):
        if not self.line_ids:
            return True
        for template_line in self.line_ids:
            if template_line.amount:
                return True
        return False

    @api.multi
    def load_lines(self):
        self.ensure_one()
        template = self.template_id
        for line in template.template_line_ids:
            if line.type == 'input':
                self.env['wizard.select.move.template.line'].create({
                    'template_id': self.id,
                    'sequence': line.sequence,
                    'name': line.name,
                    'amount': 0.0,
                    'account_id': line.account_id.id,
                    'move_line_type': line.move_line_type,
                })
        if not self.line_ids:
            return self.load_template()
        self.state = 'template_selected'

        view_rec = self.env['ir.model.data'].get_object_reference(
            'account_move_template', 'wizard_select_template')
        view_id = view_rec and view_rec[1] or False

        return {
            'view_type': 'form',
            'view_id': [view_id],
            'view_mode': 'form',
            'res_model': 'wizard.select.move.template',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def load_template(self):
        self.ensure_one()
        account_period_model = self.env['account.period']
        if not self.check_zero_lines():
            raise exceptions.Warning(
                _('At least one amount has to be non-zero!')
            )
        input_lines = {}
        for template_line in self.line_ids:
            input_lines[template_line.sequence] = template_line.amount

        period = account_period_model.find()
        if not period:
            raise exceptions.Warning(_('Unable to find a valid period !'))

        computed_lines = self.template_id.compute_lines(input_lines)

        moves = {}
        for line in self.template_id.template_line_ids:
            if line.journal_id.id not in moves:
                moves[line.journal_id.id] = self._make_move(
                    self.template_id.name,
                    period.id,
                    line.journal_id.id,
                    self.partner_id.id
                )

            self._make_move_line(
                line,
                computed_lines,
                moves[line.journal_id.id],
                period.id,
                self.partner_id.id
            )
            if self.template_id.cross_journals:
                trans_account_id = self.template_id.transitory_acc_id.id
                self._make_transitory_move_line(
                    line,
                    computed_lines,
                    moves[line.journal_id.id],
                    period.id,
                    trans_account_id,
                    self.partner_id.id
                )

        return {
            'domain': "[('id','in', " + str(moves.values()) + ")]",
            'name': 'Entries',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model
    def _make_move(self, ref, period_id, journal_id, partner_id):
        move = self.env['account.move'].create({
            'ref': ref,
            'period_id': period_id,
            'journal_id': journal_id,
            'partner_id': partner_id,
        })
        return move.id

    @api.model
    def _make_move_line(self, line, computed_lines,
                        move_id, period_id, partner_id):
        account_move_line_model = self.env['account.move.line']
        analytic_account_id = False
        if line.analytic_account_id:
            if not line.journal_id.analytic_journal_id:
                raise exceptions.Warning(
                    _("You have to define an analytic "
                      "journal on the '%s' journal!")
                    % (line.journal_id.name,)
                )

            analytic_account_id = line.analytic_account_id.id
        vals = {
            'name': line.name,
            'move_id': move_id,
            'journal_id': line.journal_id.id,
            'period_id': period_id,
            'analytic_account_id': analytic_account_id,
            'account_id': line.account_id.id,
            'date': time.strftime('%Y-%m-%d'),
            'account_tax_id': line.account_tax_id.id,
            'credit': 0.0,
            'debit': 0.0,
            'partner_id': partner_id,
        }
        if line.move_line_type == 'cr':
            vals['credit'] = computed_lines[line.sequence]
        if line.move_line_type == 'dr':
            vals['debit'] = computed_lines[line.sequence]
        id_line = account_move_line_model.create(vals)
        return id_line

    @api.model
    def _make_transitory_move_line(self, line,
                                   computed_lines, move_id, period_id,
                                   trans_account_id, partner_id):
        account_move_line_model = self.env['account.move.line']
        analytic_account_id = False
        if line.analytic_account_id:
            if not line.journal_id.analytic_journal_id:
                raise exceptions.Warning(
                    _('No Analytic Journal !'),
                    _("You have to define an analytic journal "
                      "on the '%s' journal!")
                    % (line.template_id.journal_id.name,)
                )
            analytic_account_id = line.analytic_account_id.id
        vals = {
            'name': 'transitory',
            'move_id': move_id,
            'journal_id': line.journal_id.id,
            'period_id': period_id,
            'analytic_account_id': analytic_account_id,
            'account_id': trans_account_id,
            'date': time.strftime('%Y-%m-%d'),
            'partner_id': partner_id,
        }
        if line.move_line_type != 'cr':
            vals['credit'] = computed_lines[line.sequence]
        if line.move_line_type != 'dr':
            vals['debit'] = computed_lines[line.sequence]
        id_line = account_move_line_model.create(vals)
        return id_line


class WizardSelectMoveTemplateLine(models.TransientModel):
    _description = 'Template Lines'
    _name = "wizard.select.move.template.line"

    template_id = fields.Many2one(
        comodel_name='wizard.select.move.template',
        string='Template'
    )
    sequence = fields.Integer(string='Number', required=True)
    name = fields.Char(required=True, readonly=True)
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        required=True,
        readonly=True
    )
    move_line_type = fields.Selection(
        [('cr', 'Credit'), ('dr', 'Debit')],
        string='Move Line Type',
        required=True,
        readonly=True
    )
    amount = fields.Float(required=True)
