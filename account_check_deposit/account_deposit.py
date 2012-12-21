# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   account_check_deposit for OpenERP                                         #
#   Copyright (C) 2012 Akretion Benoît GUILLOT <benoit.guillot@akretion.com>  #
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

from openerp.osv import fields
from openerp.osv.orm import Model

class account_check_deposit(Model):
    _name = "account.check.deposit"
    _description = "Account Check Deposit"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'check_payment_ids': fields.one2many('account.move.line', 'check_deposit_id', 'Check Payments'),
        'deposit_date': fields.date('Deposit Date'),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True),
    }
    
    _defaults = {
        'name': lambda self, cr, uid, context: '/',
        'deposit_date': fields.date.context_today,
    }
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'account.check.deposit') or '/'
        return super(account_check_deposit, self).create(cr, uid, vals, context=context)
    
    def _get_check_payment_ids(self, cr, uid, ids, context=None):
        model, type_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, "account_check_deposit",
                                                                             "data_account_type_received_check")
        account_ids = self.pool.get('account.account').search(cr, uid, [('user_type', '=', type_id)], context=context)
        check_payment_ids = self.pool.get('account.move.line').search(cr, uid, [('account_id', 'in', account_ids),
                                                                                ('reconcile_id', '=', False)],
                                                                    context=context)
        return check_payment_ids
    
    def get_check_payments(self, cr, uid, ids, context=None):
        move_line_obj = self.pool.get('account.move.line')
        check_payment_ids = self._get_check_payment_ids(cr, uid, ids, context=context)
        move_line_obj.write(cr, uid, check_payment_ids, {'check_deposit_id': ids[0]}, context=context)
        return True
    
    def _prepare_account_move_vals(self, cr, uid, deposit, context=None):
        move_vals = {}
        move_lines = [[0, 0, self._prepare_sum_move_line_vals(cr, uid, deposit, move_vals, context=context)]]
        for line in deposit.check_payment_ids:
            move_lines.append([0, 0, self._prepare_move_line_vals(cr, uid, line, move_vals, context=context)])        
        move_vals.update({
            'journal_id': deposit.journal_id.id,
            'line_id': move_lines,
        })
        return move_vals
    
    def _prepare_move_line_vals(self, cr, uid, line, move_vals, context=None):
        move_line_vals = self.pool.get('account.move.line').default_get(cr, uid,
                                                        ['centralisation', 'date','date_created',
                                                         'currency_id', 'journal_id', 'amount_currency',
                                                         'account_id', 'period_id', 'company_id'],
                                                        context=context)
        move_line_vals.update({
            'name': line.ref, #name ?
            'credit': line.debit,
            'account_id': line.account_id.id,
        })
        move_lines_vals.append(move_line_vals)
        return move_line_vals
    
    def _prepare_sum_move_line_vals(self, cr, uid, deposit, move_vals, context=None):
        move_line_vals = self.pool.get('account.move.line').default_get(cr, uid,
                                                            ['centralisation', 'date','date_created',
                                                             'currency_id', 'journal_id', 'amount_currency',
                                                             'account_id', 'period_id', 'company_id', 'state'],
                                                            context=context)
        debit = 0.0
        for line in deposit.check_payment_ids:
            debit += line.debit
        move_line_vals.update({
                'name': deposit.name,
                'debit': debit,
            })
        
        return move_line_vals
    
    def _reconcile_checks(cr, uid, deposit, move_id, context=None):
        move_line_obj = self.pool.get('account.move.line')
        for line in deposit.check_payment_ids:
            move_line_ids = move_line_obj.search(cr, uid, [('move_id', '=', move_id),
                                                            ('credit', '=', line.debit),
                                                            ('name', '=', line.ref)], context=context)
            if move_line_ids:
                move_line_obj.reconcile(cr, uid, [line.id, move_line_ids[0]], context=context)
        return True
    
    def validate_deposit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for deposit in self.browse(cr, uid, ids, context=context):
            context['journal_id'] = deposit.journal_id.id
            move_vals = self._prepare_account_move_vals(cr, uid, deposit, context=context)
            print "move_vals ====>", move_vals
            import pdb; pdb.set_trace()
            move_id = self.pool.get('account.move').create(cr, uid, move_vals, context=context)
            self.post(cr, uid, [move_id], context=context)
            self._reconcile_checks(cr, uid, deposit, move_id, context=context)
        return True
    
class account_move_line(Model):
    _inherit = "account.move.line"
    
    _columns = {
        'check_deposit_id': fields.many2one('account.check.deposit', 'Check Deposit', ondelete="restrict"),
    }
