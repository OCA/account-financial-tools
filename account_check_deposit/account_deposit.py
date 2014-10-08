# -*- coding: utf-8 -*-
###############################################################################
#
#   account_check_deposit for Odoo/OpenERP
#   Copyright (C) 2012-2014 Akretion (http://www.akretion.com/)
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

from openerp.osv import fields, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class account_check_deposit(orm.Model):
    _name = "account.check.deposit"
    _description = "Account Check Deposit"
    _order = 'deposit_date desc'

    def _compute_check_deposit(self, cr, uid, ids, name, args, context=None):
        res = {}
        for deposit in self.browse(cr, uid, ids, context=context):
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
            res[deposit.id] = {
                'total_amount': total,
                'is_reconcile': reconcile,
                'currency_none_same_company_id': currency_none_same_company_id,
                'check_count': count,
                }
        return res

    _columns = {
        'name': fields.char(
            'Name', size=64, readonly=True),
        'check_payment_ids': fields.one2many(
            'account.move.line', 'check_deposit_id', 'Check Payments',
            states={'done': [('readonly', '=', True)]}),
        'deposit_date': fields.date(
            'Deposit Date', required=True,
            states={'done': [('readonly', '=', True)]}),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', domain=[('type', '=', 'bank')],
            required=True, states={'done': [('readonly', '=', True)]}),
        'journal_default_account_id': fields.related(
            'journal_id', 'default_debit_account_id', type='many2one',
            relation='account.account',
            string='Default Debit Account of the Journal'),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True,
            states={'done': [('readonly', '=', True)]}),
        'currency_none_same_company_id': fields.function(
            _compute_check_deposit, type='many2one',
            relation='res.currency', multi='deposit',
            string='Currency (False if same as company)'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'Status', readonly=True),
        'move_id': fields.many2one(
            'account.move', 'Journal Entry', readonly=True),
        'partner_bank_id': fields.many2one(
            'res.partner.bank', 'Bank Account', required=True,
            domain="[('company_id', '=', company_id)]",
            states={'done': [('readonly', '=', True)]}),
        'line_ids': fields.related(
            'move_id', 'line_id', relation='account.move.line',
            type='one2many', string='Lines', readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True,
            change_default=True,
            states={'done': [('readonly', '=', True)]}),
        'total_amount': fields.function(
            _compute_check_deposit, multi='deposit',
            string="Total Amount", readonly=True,
            type="float", digits_compute=dp.get_precision('Account')),
        'check_count': fields.function(
            _compute_check_deposit, multi='deposit', readonly=True,
            string="Number of Checks", type="integer"),
        'is_reconcile': fields.function(
            _compute_check_deposit, multi='deposit', readonly=True,
            string="Reconcile", type="boolean"),
    }

    _defaults = {
        'name': '/',
        'deposit_date': fields.date.context_today,
        'state': 'draft',
        'company_id': lambda self, cr, uid, c: self.pool['res.company'].
        _company_default_get(cr, uid, 'account.check.deposit', context=c),
    }

    def _check_deposit(self, cr, uid, ids):
        for deposit in self.browse(cr, uid, ids):
            deposit_currency = deposit.currency_id
            if deposit_currency == deposit.company_id.currency_id:
                for line in deposit.check_payment_ids:
                    if line.currency_id:
                        raise orm.except_orm(
                            _('Error:'),
                            _("The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s.") % (
                                line.debit, line.ref or '',
                                line.currency_id.name,
                                deposit_currency.name))
            else:
                for line in deposit.check_payment_ids:
                    if line.currency_id != deposit_currency:
                        raise orm.except_orm(
                            _('Error:'),
                            _("The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s.") % (
                                line.debit, line.ref or '',
                                line.currency_id.name,
                                deposit_currency.name))
        return True

    _constraints = [(
        _check_deposit,
        "All the checks of the deposit must be in the currency of the deposit",
        ['currency_id', 'check_payment_ids', 'company_id']
        )]

    def unlink(self, cr, uid, ids, context=None):
        for deposit in self.browse(cr, uid, ids, context=context):
            if deposit.state == 'done':
                raise orm.except_orm(
                    _('Error!'),
                    _("The deposit '%s' is in valid state, so you must "
                        "cancel it before deleting it.")
                    % deposit.name)
        return super(account_check_deposit, self).unlink(
            cr, uid, ids, context=context)

    def backtodraft(self, cr, uid, ids, context=None):
        for deposit in self.browse(cr, uid, ids, context=context):
            if deposit.move_id:
                # It will raise here if journal_id.update_posted = False
                deposit.move_id.button_cancel()
                for line in deposit.check_payment_ids:
                    if line.reconcile_id:
                        line.reconcile_id.unlink()
                deposit.move_id.unlink()
            deposit.write({'state': 'draft'})
        return True

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool['ir.sequence'].\
                next_by_code(cr, uid, 'account.check.deposit')
        return super(account_check_deposit, self).\
            create(cr, uid, vals, context=context)

    def _prepare_account_move_vals(self, cr, uid, deposit, context=None):
        date = deposit.deposit_date
        period_obj = self.pool['account.period']
        period_ids = period_obj.find(cr, uid, dt=date, context=context)
        # period_ids will always have a value, cf the code of find()
        move_vals = {
            'journal_id': deposit.journal_id.id,
            'date': date,
            'period_id': period_ids[0],
            'name': _('Check Deposit %s') % deposit.name,
            'ref': deposit.name,
            }
        return move_vals

    def _prepare_move_line_vals(
            self, cr, uid, line, context=None):
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

    def _prepare_counterpart_move_lines_vals(
            self, cr, uid, deposit, total_debit, total_amount_currency,
            context=None):
        return {
            'name': _('Check Deposit %s') % deposit.name,
            'debit': total_debit,
            'credit': 0.0,
            'account_id': deposit.company_id.check_deposit_account_id.id,
            'partner_id': False,
            'currency_id': deposit.currency_none_same_company_id.id or False,
            'amount_currency': total_amount_currency,
            }

    def validate_deposit(self, cr, uid, ids, context=None):
        am_obj = self.pool['account.move']
        aml_obj = self.pool['account.move.line']
        if context is None:
            context = {}
        for deposit in self.browse(cr, uid, ids, context=context):
            move_vals = self._prepare_account_move_vals(
                cr, uid, deposit, context=context)
            context['journal_id'] = move_vals['journal_id']
            context['period_id'] = move_vals['period_id']
            move_id = am_obj.create(cr, uid, move_vals, context=context)
            total_debit = 0.0
            total_amount_currency = 0.0
            to_reconcile_line_ids = []
            for line in deposit.check_payment_ids:
                total_debit += line.debit
                total_amount_currency += line.amount_currency
                line_vals = self._prepare_move_line_vals(
                    cr, uid, line, context=context)
                line_vals['move_id'] = move_id
                move_line_id = aml_obj.create(
                    cr, uid, line_vals, context=context)
                to_reconcile_line_ids.append([line.id, move_line_id])

            # Create counter-part
            if not deposit.company_id.check_deposit_account_id:
                raise orm.except_orm(
                    _('Configuration Error:'),
                    _("Missing Account for Check Deposits on the "
                        "company '%s'.") % deposit.company_id.name)

            counter_vals = self._prepare_counterpart_move_lines_vals(
                cr, uid, deposit, total_debit, total_amount_currency,
                context=context)
            counter_vals['move_id'] = move_id
            aml_obj.create(cr, uid, counter_vals, context=context)

            am_obj.post(cr, uid, [move_id], context=context)
            deposit.write({'state': 'done', 'move_id': move_id})
            # We have to reconcile after post()
            for reconcile_line_ids in to_reconcile_line_ids:
                aml_obj.reconcile(
                    cr, uid, reconcile_line_ids, context=context)
        return True

    def onchange_company_id(
            self, cr, uid, ids, company_id, currency_id, context=None):
        vals = {}
        if company_id:
            company = self.pool['res.company'].browse(
                cr, uid, company_id, context=context)
            if currency_id:
                if company.currency_id.id == currency_id:
                    vals['currency_none_same_company_id'] = False
                else:
                    vals['currency_none_same_company_id'] = currency_id
            partner_bank_ids = self.pool['res.partner.bank'].search(
                cr, uid, [('company_id', '=', company_id)], context=context)
            if len(partner_bank_ids) == 1:
                vals['partner_bank_id'] = partner_bank_ids[0]
        else:
            vals['currency_none_same_company_id'] = False
            vals['partner_bank_id'] = False
        return {'value': vals}

    def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
        vals = {}
        if journal_id:
            journal = self.pool['account.journal'].browse(
                cr, uid, journal_id, context=context)
            vals['journal_default_account_id'] = \
                journal.default_debit_account_id.id
            if journal.currency:
                vals['currency_id'] = journal.currency.id
            else:
                vals['currency_id'] = journal.company_id.currency_id.id
        else:
            vals['journal_default_account_id'] = False
        return {'value': vals}

    def onchange_currency_id(
            self, cr, uid, ids, currency_id, company_id, context=None):
        vals = {}
        if currency_id and company_id:
            company = self.pool['res.company'].browse(
                cr, uid, company_id, context=context)
            if company.currency_id.id == currency_id:
                vals['currency_none_same_company_id'] = False
            else:
                vals['currency_none_same_company_id'] = currency_id
        else:
            vals['currency_none_same_company_id'] = False
        return {'value': vals}


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    _columns = {
        'check_deposit_id': fields.many2one(
            'account.check.deposit',
            'Check Deposit'),
    }


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'check_deposit_account_id': fields.many2one(
            'account.account', 'Account for Check Deposits',
            domain=[
                ('type', '<>', 'view'),
                ('type', '<>', 'closed'),
                ('reconcile', '=', True)]),
        }
