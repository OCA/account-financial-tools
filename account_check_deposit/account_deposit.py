# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   account_check_deposit for OpenERP                                         #
#   Copyright (C) 2012 Akretion Benoît GUILLOT <benoit.guillot@akretion.com>  #
#   Copyright (C) 2013 Akretion Chafique DELLI <chafique.delli@akretion.com>  #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


class account_check_deposit(orm.Model):
    _name = "account.check.deposit"
    _description = "Account Check Deposit"

    def sum_amount(self, cr, uid, ids, name, args, context=None):
        res = {}
        for deposit in self.browse(cr, uid, ids, context=context):
            total = 0
            for line in deposit.check_payment_ids:
                total += line.debit
            res[deposit.id]= total
        return  res

    def _is_reconcile(self, cr, uid, ids, name, args, context=None):
        res = {}
        for deposit in self.browse(cr, uid, ids, context=context):
            res[deposit.id] = False
            if deposit.move_id:
                for line in deposit.move_id.line_id:
                    if line.debit > 0 and line.reconcile_id:
                        res[deposit.id] = True
        return res 

    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True,
                            states={'draft':[('readonly',False)]}),
        'check_payment_ids': fields.one2many('account.move.line',
                                              'check_deposit_id',
                                              'Check Payments',
                                              readonly=True,
                                              states={'draft':[('readonly',False)]}),
        'deposit_date': fields.date('Deposit Date', readonly=True,
                                    states={'draft':[('readonly',False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal',
                                      required=True, readonly=True,
                                      states={'draft':[('readonly',False)]}),
        'state': fields.selection([
            ('draft','Draft'),
            ('done','Done'),
        ],'Status', readonly=True),
        'move_id': fields.many2one('account.move', 'Journal Entry',
                                   readonly=True,
                                   states={'draft':[('readonly',False)]}),
        'bank_id': fields.many2one('res.partner.bank', 'Bank', required=True,
                                   readonly=True,
                                   domain="[('partner_id', '=', partner_id)]",
                                   states={'draft':[('readonly',False)]}),
        'line_ids': fields.related('move_id', 'line_id', 
            relation='account.move.line',
            type='one2many',
            string='Lines',
            readonly=True,
            ),
        'partner_id':fields.related('company_id', 'partner_id', type="many2one",
                                    relation="res.partner", string="Partner",
                                    readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      change_default=True, readonly=True,
                                      states={'draft':[('readonly',False)]}),
        'total_amount': fields.function(sum_amount, string ="total amount", type="float"),
        'is_reconcile': fields.function(_is_reconcile, string ="Reconcile", type="boolean"),
    }

    _defaults = {
        'name': lambda self, cr, uid, context: '/',
        'deposit_date': fields.date.context_today,
        'state':'draft',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.check.deposit', context=c),
    }

    def unlink(self, cr, uid, ids, context=None):
        for deposit in self.browse(cr, uid, ids, context=context):
            if deposit.state == 'done':
                raise osv.except_osv(_('User Error!'),
                    _('You cannot delete a validad deposit, cancel it before'))
        return super(account_check_deposit, self).unlink(cr, uid, ids, context=context)

    def cancel(self, cr, uid, ids, context=None):
        for deposit in self.browse(cr, uid, ids, context=context):
            if not deposit.journal_id.update_posted:
                raise osv.except_osv(_('Error!'), _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
            for line in deposit.check_payment_ids:
                if line.reconcile_id:
                    line.reconcile_id.unlink()
            if deposit.move_id:
                deposit.move_id.button_cancel()
                deposit.move_id.unlink()
            deposit.write({'state': 'draft'})
        return True

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'account.check.deposit') or '/'
        return super(account_check_deposit, self).create(cr, uid, vals, context=context)

    def _prepare_account_move_vals(self, cr, uid, deposit, context=None):
        move_vals = {
            'journal_id': deposit.journal_id.id,
            'date': deposit.deposit_date,
            }
        period_obj = self.pool['account.period']
        period_ids =  period_obj.find(cr, uid, dt=deposit.deposit_date, context=context)
        if period_ids:
            move_vals['period_id'] = period_ids[0]

        move_lines = [[0, 0, self._prepare_sum_move_line_vals(cr, uid, deposit,
                                                              move_vals,
                                                              context=context)]]
        for line in deposit.check_payment_ids:
            move_lines.append([0, 0, self._prepare_move_line_vals(cr, uid, line,
                                                                  move_vals,
                                                                  context=context)])
        move_vals.update({'line_id': move_lines})
        return move_vals

    def _prepare_move_line_vals(self, cr, uid, line, move_vals, context=None):
        move_line_vals = self.pool.get('account.move.line').default_get(
            cr, uid,
            ['centralisation', 'date','date_created', 'currency_id',
             'journal_id', 'amount_currency', 'account_id', 'period_id',
             'company_id'],
            context=context)
        move_line_vals.update({
            'name': line.ref,
            'credit': line.debit,
            'account_id': line.account_id.id,
            'partner_id': line.partner_id.id,
            'check_line_id': line.id,
        })
        return move_line_vals

    def _prepare_sum_move_line_vals(self, cr, uid, deposit, move_vals, context=None):
        move_line_vals = self.pool.get('account.move.line').default_get(
            cr, uid,
            ['centralisation', 'date','date_created', 'currency_id',
             'journal_id', 'amount_currency', 'account_id', 'period_id',
             'company_id', 'state'],
            context=context)

        debit = 0.0
        for line in deposit.check_payment_ids:
            debit += line.debit
        move_line_vals.update({
                'name': deposit.name,
                'debit': debit,
                'ref': deposit.name,
            })

        return move_line_vals

    def _reconcile_checks(self, cr, uid, move_id, context=None):
        move_line_obj = self.pool['account.move.line']
        move_obj = self.pool['account.move']
        move = move_obj.browse(cr, uid, move_id, context=context)
        for line in move.line_id:
            if line.check_line_id:
                move_line_obj.reconcile(cr, uid,
                                        [line.id, line.check_line_id.id],
                                        context=context)
        return True



    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        vals={}
        if company_id:
            company=self.pool.get('res.company').browse(cr, uid, company_id, context=context)
        vals['partner_id']=company.partner_id.id
        return {'value':vals}



    def validate_deposit(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for deposit in self.browse(cr, uid, ids, context=context):
            context['journal_id'] = deposit.journal_id.id
            move_vals = self._prepare_account_move_vals(cr, uid, deposit, context=context)
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            move_obj.post(cr, uid, [move_id], context=context)
            self._reconcile_checks(cr, uid, move_id, context=context)
            deposit.write({'state':'done', 'move_id': move_id})
        return True


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    _columns = {
        'check_deposit_id': fields.many2one('account.check.deposit',
                                             'Check Deposit'),
        'check_line_id': fields.many2one('account.move.line',
                                             'Check Receive Move line'),
    }
