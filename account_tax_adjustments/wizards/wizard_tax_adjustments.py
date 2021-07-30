# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.addons.account.wizard.wizard_tax_adjustments import TaxAdjustments as taxadjustments

import logging
_logger = logging.getLogger(__name__)


class TaxAdjustments(models.TransientModel):
    _inherit = 'tax.adjustments.wizard'

    note = fields.Text('Description')
    template_id = fields.Many2one(comodel_name='tax.adjustment.template', string='Get from template')
    date_range_id = fields.Many2one(comodel_name='date.range', string='Date range')
    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to', default=fields.Date.today())
    company_id = fields.Many2one('res.company', default=lambda self:
                                 self.env['res.company']._company_default_get('tax.adjustments.wizard'),
                                 required=False, string='Company')
    choice_period_type = fields.Selection([
        ('month', 'Fiscal month'),
        ('year', 'Fiscal year'),
    ], string='Type period', default='month')
    unsigned_amount = fields.Monetary(currency_field='company_currency_id')
    post = fields.Boolean(string='Post after create', default=True)

    @api.model
    def default_get(self, var_fields):
        res = super(TaxAdjustments, self).default_get(var_fields)
        company_id = self.env['res.company']._company_default_get('tax.adjustments.wizard')
        date = self._context.get('default_date') or fields.Date.context_today(self)
        choice_period_type = self._context.get('default_choice_period_type') or 'month'
        res.update({
            'debit_account_id': self._context.get('default_debit_account_id'),
            'credit_account_id': self._context.get('default_credit_account_id'),
            'adjustment_type': self._context.get('default_adjustment_type'),
            'journal_id': self.env['account.journal'].search([('type', '=', 'general'), ('company_id', '=', company_id.id)], limit=1).id,
            'company_id': company_id.id,
            'date': date,
            'choice_period_type': choice_period_type,
        })
        if date and choice_period_type and company_id:
            # accounting_date = fields.Date.from_string(date)

            date_range_id = False
            if choice_period_type == 'month':
                date_range_id = company_id.find_daterange_fm(date)
            elif choice_period_type == 'year':
                date_range_id = company_id.find_daterange_fy(date)
            if date_range_id:
                res.update({
                    'date_range_id': date_range_id.id,
                    'date_from': date_range_id.date_start,
                    'date_to': date_range_id.date_end,
                })
        return res

    def auto_complete(self, fields, update):
        res = self.default_get(fields)
        res.update(update)
        record = self.create(res)
        record._onchange_date()
        if record.adjustment_type == 'credit':
            return self.create_move_credit()['res_id']
        elif record.adjustment_type == 'debit':
            return self.create_move_debit()['res_id']
        return False

    @api.one
    def _get_account_id(self):
        account_id = False
        if self.adjustment_type == 'debit':
            account_id = self.credit_account_id
        elif self.adjustment_type == 'credit':
            account_id = self.debit_account_id
        return account_id

    @api.onchange('template_id')
    def _onchange_template_id(self):
        for record in self:
            if record.template_id:
                record.reason = record.template_id.reason
                record.choice_period_type = record.template_id.choice_period_type
                record.journal_id = record.template_id.journal_id
                record.debit_account_id = record.template_id.debit_account_id
                record.credit_account_id = record.template_id.credit_account_id
                record.tax_id = record.template_id.tax_id

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        """Handle date range change."""
        for record in self:
            record.date_from = record.date_range_id.date_start
            record.date_to = record.date_range_id.date_end

            account_id = False
            if record.adjustment_type == 'debit':
                account_id = record.credit_account_id
            elif record.adjustment_type == 'credit':
                account_id = record.debit_account_id
            if not self._context.get('block_change', False):
                amount = record.calculate_amount(record._get_account_id()[0], record.date_from, record.date_to, company_id=record.company_id.id)
                record.amount = abs(amount)
                record.unsigned_amount = amount

    @api.onchange('date', 'choice_period_type', 'company_id')
    @api.depends('amount', 'unsigned_amount', 'date_range_id', 'date_from', 'date_to')
    def _onchange_date(self):
        for record in self:
            if record.date:
                accounting_date = fields.Date.from_string(record.date)
                if record.choice_period_type == 'month':
                    record.with_context(dict(self._context, block_change=True)).date_range_id = record.company_id.find_daterange_fm(accounting_date)
                elif record.choice_period_type == 'year':
                    record.with_context(dict(self._context, block_change=True)).date_range_id = record.company_id.find_daterange_fy(accounting_date)
                if record.date_range_id:
                    record.date_from = record.date_range_id.date_start
                    record.date_to = record.date_range_id.date_end

            amount = record.calculate_amount(record._get_account_id()[0], record.date_from, record.date_to, company_id=record.company_id.id)
            record.amount = abs(amount)
            record.unsigned_amount = amount
            if record.company_id:
                record.company_currency_id = record.company_id.currency_id

    @api.model
    def calculate_amount(self, account_id, date_from, date_to, company_id=None):
        # _logger.info("ACCOUNT %s" % account_id)
        if not account_id:
            return 0.0
        if not date_from or not date_to:
            return 0.0
        if company_id is None:
            company_id = self.company_id.id
        domain = [('account_id', '=', account_id.id)]
        # move = self.env['account.move.line'].search(domain)
        domain += [('move_id.date', '>=', date_from), ('move_id.date', '<=', date_to)]
        domain += [('company_id', '=', company_id), ('move_id.state', '=', 'posted')]
        move_fiscal = self.env['account.move.line'].search(domain)
        # _logger.info("MOVES (%s) %s" % (domain, [x.balance for x in move_fiscal]))
        amount = sum([x.balance for x in move_fiscal])
        return amount

    @api.model
    def _create_move_value(self):
        adjustment_type = self.env.context.get('adjustment_type', (self.amount > 0.0 and 'debit' or 'credit'))
        debit_vals = {
            'name': self.reason,
            'debit': abs(self.amount),
            'credit': 0.0,
            'account_id': self.debit_account_id.id,
            'tax_line_id': adjustment_type == 'debit' and self.tax_id.id or False,
        }
        credit_vals = {
            'name': self.reason,
            'debit': 0.0,
            'credit': abs(self.amount),
            'account_id': self.credit_account_id.id,
            'tax_line_id': adjustment_type == 'credit' and self.tax_id.id or False,
        }
        vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'state': 'draft',
            'ref': "%s%s" % (self.reason, self.date_range_id and " (%s)" % self.date_range_id.name or ""),
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        return vals

    @api.multi
    def _create_move(self):
        move = self.env['account.move'].create(self._create_move_value())
        for record in self:
            if record.post:
                move.post()
        return move.id

taxadjustments._create_move = TaxAdjustments._create_move
