# -*- coding: utf-8 -*-
###############################################################################
#
#   account_check_deposit for Odoo
#   Copyright (C) 2012-2015 Akretion (http://www.akretion.com/)
#   @author: Benoît GUILLOT <benoit.guillot@akretion.com>
#   @author: Chafique DELLI <chafique.delli@akretion.com>
#   @author: Alexis de Lattre <alexis.delattre@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning as UserError


class AccountCheckDeposit(models.Model):
    _name = "account.check.deposit"
    _description = "Account Check Deposit"
    _order = 'deposit_date desc'

    @api.multi
    @api.depends(
        'company_id', 'currency_id', 'check_payment_ids.debit',
        'check_payment_ids.amount_currency',
        'move_id.line_id.reconcile_id')
    def _compute_check_deposit(self):
        for deposit in self:
            total = 0.0
            count = 0
            reconcile = False
            currency_none_same_company_id = False
            if deposit.company_id.currency_id != deposit.currency_id:
                currency_none_same_company_id = deposit.currency_id.id
            for line in deposit.check_payment_ids:
                count += 1
                if currency_none_same_company_id:
                    total += line.amount_currency
                else:
                    total += line.debit
            if deposit.move_id:
                for line in deposit.move_id.line_id:
                    if line.debit > 0 and line.reconcile_id:
                        reconcile = True
            deposit.total_amount = total
            deposit.is_reconcile = reconcile
            deposit.currency_none_same_company_id =\
                currency_none_same_company_id
            deposit.check_count = count

    name = fields.Char(string='Name', size=64, readonly=True, default='/')
    check_payment_ids = fields.One2many(
        'account.move.line', 'check_deposit_id', string='Check Payments',
        states={'done': [('readonly', '=', True)]})
    deposit_date = fields.Date(
        string='Deposit Date', required=True,
        states={'done': [('readonly', '=', True)]},
        default=fields.Date.context_today)
    journal_id = fields.Many2one(
        'account.journal', string='Journal', domain=[('type', '=', 'bank')],
        required=True, states={'done': [('readonly', '=', True)]})
    journal_default_account_id = fields.Many2one(
        'account.account', related='journal_id.default_debit_account_id',
        string='Default Debit Account of the Journal', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        states={'done': [('readonly', '=', True)]})
    currency_none_same_company_id = fields.Many2one(
        'res.currency', compute='_compute_check_deposit',
        string='Currency (False if same as company)')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], string='Status', default='draft', readonly=True)
    move_id = fields.Many2one(
        'account.move', string='Journal Entry', readonly=True)
    partner_bank_id = fields.Many2one(
        'res.partner.bank', string='Bank Account', required=True,
        domain="[('company_id', '=', company_id)]",
        states={'done': [('readonly', '=', True)]})
    line_ids = fields.One2many(
        'account.move.line', related='move_id.line_id',
        string='Lines', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        states={'done': [('readonly', '=', True)]},
        default=lambda self: self.env['res.company']._company_default_get(
            'account.check.deposit'))
    total_amount = fields.Float(
        compute='_compute_check_deposit',
        string="Total Amount", readonly=True,
        digits=dp.get_precision('Account'))
    check_count = fields.Integer(
        compute='_compute_check_deposit', readonly=True,
        string="Number of Checks")
    is_reconcile = fields.Boolean(
        compute='_compute_check_deposit', readonly=True,
        string="Reconcile")

    @api.multi
    @api.constrains('currency_id', 'check_payment_ids', 'company_id')
    def _check_deposit(self):
        for deposit in self:
            deposit_currency = deposit.currency_id
            if deposit_currency == deposit.company_id.currency_id:
                for line in deposit.check_payment_ids:
                    if line.currency_id:
                        raise ValidationError(
                            _("The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s.") % (
                                line.debit, line.ref or '',
                                line.currency_id.name,
                                deposit_currency.name))
            else:
                for line in deposit.check_payment_ids:
                    if line.currency_id != deposit_currency:
                        raise ValidationError(
                            _("The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s.") % (
                                line.debit, line.ref or '',
                                line.currency_id.name,
                                deposit_currency.name))

    @api.multi
    def unlink(self):
        for deposit in self:
            if deposit.state == 'done':
                raise UserError(
                    _("The deposit '%s' is in valid state, so you must "
                        "cancel it before deleting it.")
                    % deposit.name)
        return super(AccountCheckDeposit, self).unlink()

    @api.multi
    def backtodraft(self):
        for deposit in self:
            if deposit.move_id:
                # It will raise here if journal_id.update_posted = False
                deposit.move_id.button_cancel()
                for line in deposit.check_payment_ids:
                    if line.reconcile_id:
                        line.reconcile_id.unlink()
                deposit.move_id.unlink()
            deposit.write({'state': 'draft'})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].\
                next_by_code('account.check.deposit')
        return super(AccountCheckDeposit, self).create(vals)

    @api.model
    def _prepare_account_move_vals(self, deposit):
        date = deposit.deposit_date
        period_obj = self.env['account.period']
        period_ids = period_obj.find(dt=date)
        # period_ids will always have a value, cf the code of find()
        move_vals = {
            'journal_id': deposit.journal_id.id,
            'date': date,
            'period_id': period_ids[0].id,
            'name': _('Check Deposit %s') % deposit.name,
            'ref': deposit.name,
            }
        return move_vals

    @api.model
    def _prepare_move_line_vals(self, line):
        assert (line.debit > 0), 'Debit must have a value'
        return {
            'name': _('Check Deposit - Ref. Check %s') % line.ref,
            'credit': line.debit,
            'debit': 0.0,
            'account_id': line.account_id.id,
            'partner_id': line.partner_id.id,
            'currency_id': line.currency_id.id or False,
            'amount_currency': line.amount_currency * -1,
            }

    @api.model
    def _prepare_counterpart_move_lines_vals(
            self, deposit, total_debit, total_amount_currency):
        return {
            'name': _('Check Deposit %s') % deposit.name,
            'debit': total_debit,
            'credit': 0.0,
            'account_id': deposit.company_id.check_deposit_account_id.id,
            'partner_id': False,
            'currency_id': deposit.currency_none_same_company_id.id or False,
            'amount_currency': total_amount_currency,
            }

    @api.multi
    def validate_deposit(self):
        am_obj = self.env['account.move']
        aml_obj = self.env['account.move.line']
        for deposit in self:
            move_vals = self._prepare_account_move_vals(deposit)
            move = am_obj.create(move_vals)
            total_debit = 0.0
            total_amount_currency = 0.0
            to_reconcile_lines = []
            for line in deposit.check_payment_ids:
                total_debit += line.debit
                total_amount_currency += line.amount_currency
                line_vals = self._prepare_move_line_vals(line)
                line_vals['move_id'] = move.id
                move_line = aml_obj.create(line_vals)
                to_reconcile_lines.append(line + move_line)

            # Create counter-part
            if not deposit.company_id.check_deposit_account_id:
                raise UserError(
                    _("Missing Account for Check Deposits on the "
                        "company '%s'.") % deposit.company_id.name)

            counter_vals = self._prepare_counterpart_move_lines_vals(
                deposit, total_debit, total_amount_currency)
            counter_vals['move_id'] = move.id
            aml_obj.create(counter_vals)

            move.post()
            deposit.write({'state': 'done', 'move_id': move.id})
            # We have to reconcile after post()
            for reconcile_lines in to_reconcile_lines:
                reconcile_lines.reconcile()
        return True

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            partner_banks = self.env['res.partner.bank'].search(
                [('company_id', '=', self.company_id.id)])
            if len(partner_banks) == 1:
                self.partner_bank_id = partner_banks[0]
        else:
            self.partner_bank_id = False

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            if self.journal_id.currency:
                self.currency_id = self.journal_id.currency
            else:
                self.currency_id = self.journal_id.company_id.currency_id


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    check_deposit_id = fields.Many2one(
        'account.check.deposit', string='Check Deposit', copy=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    check_deposit_account_id = fields.Many2one(
        'account.account', string='Account for Check Deposits', copy=False,
        domain=[
            ('type', '<>', 'view'),
            ('type', '<>', 'closed'),
            ('reconcile', '=', True)])
