# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
import time
from odoo.tools.float_utils import float_round as round

import logging
_logger = logging.getLogger(__name__)


class WizardSelectMoveTemplate(models.TransientModel):
    _name = "wizard.select.move.template"

    template_id = fields.Many2one('account.move.template', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    line_ids = fields.One2many(
        'wizard.select.move.template.line', 'template_id')
    state = fields.Selection(
        [('template_selected', 'Template selected')], 'State')
    date_range_id = fields.Many2one(comodel_name='date.range', string='Date range')
    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to', default=fields.Date.today())
    amount_input = fields.Float("Holder for default amount")
    date_due = fields.Date('Due Date', default=fields.Date.today())
    accounting_date = fields.Date('Accounting Date', default=fields.Date.today())
    company_id = fields.Many2one('res.company', default=lambda self:
                                 self.env['res.company']._company_default_get('wizard.select.move.template'),
                                 required=False, string='Company')
    choice_period_type = fields.Selection([
        ('month', 'Fiscal month'),
        ('year', 'Fiscal year'),
    ], string='Type period', default='year')
    post = fields.Boolean('Post after generate', help="After generate account move post and close without open it.")

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        """Handle date range change."""
        for record in self:
            record.date_from = record.date_range_id.date_start
            record.date_to = record.date_range_id.date_end

    @api.onchange('accounting_date', 'choice_period_type', 'company_id')
    def _onchange_accounting_date(self):
        for record in self:
            if record.accounting_date:
                accounting_date = fields.Date.from_string(record.accounting_date)
                if record.choice_period_type == 'month':
                    record.date_range_id = record.company_id.find_daterange_fm(accounting_date)
                elif record.choice_period_type == 'year':
                    record.date_range_id = record.company_id.find_daterange_fy(accounting_date)
                if record.date_range_id:
                    record.date_from = record.date_range_id.date_start
                    record.date_to = record.date_range_id.date_end
                record.date_due = record.accounting_date

    @api.model
    def default_get(self, fields_list):
        res = super(WizardSelectMoveTemplate, self).default_get(fields_list)
        if not res:
            res = {}
        company_id = self.env['res.company']._company_default_get('wizard.select.move.template')
        accounting_date = self._context.get('default_accounting_date')
        choice_period_type = self._context.get('default_choice_period_type')
        res.update({
            'accounting_date': accounting_date,
            'date_due': accounting_date,
            'date_range_id': self._context.get('default_date_range_id'),
            'date_from': self._context.get('default_date_from'),
            'date_to': self._context.get('default_date_to'),
            'amount_input': self._context.get('default_amount_input', 0.0),
            'partner_id': self._context.get('default_partner_id'),
            'company_id': company_id.id,
        })
        if accounting_date and choice_period_type and company_id:
            accounting_date = fields.Date.from_string(accounting_date)
            date_range_id = False
            if choice_period_type == 'month':
                date_range_id = company_id.find_daterange_fm(accounting_date)
            elif choice_period_type == 'year':
                date_range_id = company_id.find_daterange_fy(accounting_date)
            if date_range_id:
                res.update({
                    'date_range_id': date_range_id.id,
                    'date_from': date_range_id.date_start,
                    'date_to': date_range_id.date_end,
                })
        return res

    @api.model
    def auto_complete(self, fields, update):
        res = self.default_get(fields)
        res.update(update)
        record = self.create(res)
        record.load_lines()
        return record.load_template()['context'].get('move_auto_complete', False)

    @api.multi
    def load_lines(self):
        self.ensure_one()
        lines = self.template_id.template_line_ids
        for line in lines.filtered(lambda l: l.type == 'input'):
            self.env['wizard.select.move.template.line'].create({
                'template_id': self.id,
                'sequence': line.sequence,
                'name': line.name,
                'amount': self.amount_input,
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
        if not self.date_to:
            self.date_to = fields.Date.today()
        date_to = fields.Datetime.from_string(self.date_to)
        date_from = fields.Datetime.from_string(self.date_to)
        if self.date_from:
            date_from = fields.Datetime.from_string(self.date_from)
        amounts = self.template_id.compute_lines(input_lines, date_from, date_to, partner_id=self.partner_id.id)
        name = self.template_id.name
        partner = self.partner_id.id
        moves = self.env['account.move']
        for journal in self.template_id.template_line_ids.mapped('journal_id'):
            lines = []
            move = self._create_move(name, journal.id, partner)
            moves = moves + move
            for line in self.template_id.template_line_ids.filtered(
                    lambda j: j.journal_id == journal):
                if amounts[line.sequence] == 0.0:
                    continue
                values = self._prepare_line(line, amounts, partner)
                lines.append((0, 0, values))
                # _logger.info("MOVES %s::%s" % (values, amounts[line.sequence]))
            move.with_context(dict(self._context, check_move_validity=False)).write({'line_ids': lines})
        if self.post:
            moves.post()
            return {
                "type": "ir.actions.act_window_close",
            }
        return {
            'domain': [('id', 'in', moves.ids)],
            'name': 'Entries from template: %s' % name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': dict(self._context, default_amount_input=self.amount_input, move_auto_complete=moves),
        }

    @api.model
    def _create_move(self, ref, journal_id, partner_id):
        return self.env['account.move'].create({
            'ref': ref,
            'journal_id': journal_id,
            'partner_id': partner_id,
            'date': self.accounting_date,
        })

    @api.model
    def _prepare_line(self, line, amounts, partner_id):
        company_id = self.env.user.company_id
        currency = company_id.currency_id
        prec = currency.decimal_places
        amount = round(abs(amounts[line.sequence]), prec)
        debit = line.move_line_type == 'dr'

        # if not debit and amounts[line.sequence] < 0.0:
        #     debit = True
        if line.move_line_type == 'dc' and amounts[line.sequence] > 0.0:
            debit = False
        elif line.move_line_type == 'dc' and amounts[line.sequence] < 0.0:
            debit = True
        if line.python_code and line.python_code.find('L(') != -1 and amounts[line.sequence] < 0.0:
            debit = False
        # if amount > 0 and debit:
        #     debit = False
        # if amount < 0 and not debit:
        #     debit = True
        # amount = abs(amounts[line.sequence])
        values = {
            'name': line.name,
            'journal_id': line.journal_id.id,
            'analytic_account_id': line.analytic_account_id.id,
            'analytic_tag_ids': line.analytic_tag_ids,
            'account_id': line.account_id.id,
            'date': self.accounting_date or time.strftime('%Y-%m-%d'),
            'date_maturity': self.date_due,
            'credit': not debit and amount or 0.0,
            'debit': debit and amount or 0.0,
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
        [('cr', 'Credit'), ('dr', 'Debit'), ('dc', 'Auto')], required=True, readonly=True)
    amount = fields.Float(required=True)
