# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
import time


class WizardSelectMoveTemplate(models.TransientModel):
    _name = "wizard.select.move.template"

    template_id = fields.Many2one('account.move.template', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    line_ids = fields.One2many(
        'wizard.select.move.template.line', 'template_id')
    state = fields.Selection(
        [('template_selected', 'Template selected')], 'State')

    @api.multi
    def load_lines(self):
        self.ensure_one()
        lines = self.template_id.template_line_ids
        for line in lines.filtered(lambda l: l.type == 'input'):
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
        view_rec = self.env.ref('account_move_template.wizard_select_template')
        return {
            'view_type': 'form',
            'view_id': [view_rec.id],
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
        input_lines = {}
        for template_line in self.line_ids:
            input_lines[template_line.sequence] = template_line.amount
        amounts = self.template_id.compute_lines(input_lines)
        name = self.template_id.name
        partner = self.partner_id.id
        moves = self.env['account.move']
        for journal in self.template_id.template_line_ids.mapped('journal_id'):
            lines = []
            move = self._create_move(name, journal.id, partner)
            moves = moves + move
            for line in self.template_id.template_line_ids.filtered(
                    lambda j: j.journal_id == journal):
                lines.append((0, 0,
                              self._prepare_line(line, amounts, partner)))
            move.write({'line_ids': lines})
        return {
            'domain': [('id', 'in', moves.ids)],
            'name': 'Entries from template: %s' % name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model
    def _create_move(self, ref, journal_id, partner_id):
        return self.env['account.move'].create({
            'ref': ref,
            'journal_id': journal_id,
            'partner_id': partner_id,
        })

    @api.model
    def _prepare_line(self, line, amounts, partner_id):
        debit = line.move_line_type == 'dr'
        values = {
            'name': line.name,
            'journal_id': line.journal_id.id,
            'analytic_account_id': line.analytic_account_id.id,
            'account_id': line.account_id.id,
            'date': time.strftime('%Y-%m-%d'),
            'credit': not debit and amounts[line.sequence] or 0.0,
            'debit': debit and amounts[line.sequence] or 0.0,
            'partner_id': partner_id,
        }
        return values


class WizardSelectMoveTemplateLine(models.TransientModel):
    _description = 'Template Lines'
    _name = "wizard.select.move.template.line"

    template_id = fields.Many2one(
        'wizard.select.move.template')
    sequence = fields.Integer(required=True)
    name = fields.Char(required=True, readonly=True)
    account_id = fields.Many2one(
        'account.account', required=True, readonly=True)
    move_line_type = fields.Selection(
        [('cr', 'Credit'), ('dr', 'Debit')], required=True, readonly=True)
    amount = fields.Float(required=True)
