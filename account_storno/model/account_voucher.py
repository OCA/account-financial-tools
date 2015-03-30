# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011- Slobodni programi d.o.o., Zagreb
#    Author: Goran Kliska
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
import time
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp


class account_voucher(osv.Model):
    _inherit = "account.voucher"

    # Adding support for storno accounting, negative numbers in voucher lines.
    # Amount original is taken from residual amount on accoutn move line, 
    # and amount_unreconciled and amount are calculated with abs.
    # Rewrite check if the residual amount is negative, the unreconciled and 
    # allocated amount will be negative as well.
    def recompute_voucher_lines(
            self,
            cr,
            uid,
            ids,
            partner_id,
            journal_id,
            price,
            currency_id,
            ttype,
            date,
            context=None):
        res = super(
            account_voucher,
            self).recompute_voucher_lines(
            cr,
            uid,
            ids,
            partner_id,
            journal_id,
            price,
            currency_id,
            ttype,
            date,
            context=context)
        for line in res['value']['line_cr_ids'] + res['value']['line_dr_ids']:
            if line['amount_original'] < 0:
                line['amount_unreconciled'] = line[
                    'amount_unreconciled'] * (-1)
                line['amount'] = line['amount'] * (-1)
        return res

    def first_move_line_get(
            self,
            cr,
            uid,
            voucher_id,
            move_id,
            company_currency,
            current_currency,
            context=None):
        move_line = super(
            account_voucher,
            self).first_move_line_get(
            cr,
            uid,
            voucher_id,
            move_id,
            company_currency,
            current_currency,
            context=context)
        voucher = self.pool.get('account.voucher').browse(
            cr, uid, voucher_id, context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not
        # have as based on the bank/cash journal we can not know its payment
        # or receipt
        if voucher.type in ('purchase', 'payment'):
            credit = voucher.paid_amount_in_company_currency
        elif voucher.type in ('sale', 'receipt'):
            debit = voucher.paid_amount_in_company_currency
        # if debit < 0: credit = -debit; debit = 0.0
        # if credit < 0: debit = -credit; credit = 0.0
        # sign = debit - credit < 0 and -1 or 1
        # set the first line of the voucher
        move_line['debit'] = debit
        move_line['credit'] = credit
 
        if credit > 0:
            move_line['amount_currency'] = \
                company_currency <> current_currency and -voucher.amount or 0.0
        else:
            move_line['amount_currency'] = \
                company_currency <> current_currency and voucher.amount or 0.0
 
        return move_line

    def voucher_move_line_create(
            self,
            cr,
            uid,
            voucher_id,
            line_total,
            move_id,
            company_currency,
            current_currency,
            context=None):
        moves = super(
            account_voucher,
            self).voucher_move_line_create(
            cr,
            uid,
            voucher_id,
            line_total,
            move_id,
            company_currency,
            current_currency,
            context=context)
        move_line_obj = self.pool.get('account.move.line')
        print moves
        if moves:
            for move in moves[1]:
                inv_line = voucher_line = False
                if move[0]:
                    voucher_line = move_line_obj.browse(cr, uid, move[0])
                if move[1]:
                    inv_line = move_line_obj.browse(cr, uid, move[1])
                if voucher_line and inv_line:
                    if inv_line.credit < 0:
                        move_line_obj.write(
                            cr, uid, [
                                voucher_line.id], {
                                'debit': -voucher_line.credit, 'credit': 0.0})
                    if inv_line.debit < 0:
                        move_line_obj.write(
                            cr, uid, [
                                voucher_line.id], {
                                'credit': -voucher_line.debit, 'debit': 0.0})
        return moves

    # Needs to be proposed as issue to ODOO - Allow partial reconcile unlink
    def cancel_voucher(self, cr, uid, ids, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            # refresh to make sure you don't unlink an already removed move
            voucher.refresh()
            for line in voucher.move_ids:
                if line.reconcile_id:
                    move_lines = [
                        move_line.id for move_line in line.reconcile_id.line_id]
                    move_lines.remove(line.id)
                    reconcile_pool.unlink(
                        cr, uid, [line.reconcile_id.id], context=context)
                    if len(move_lines) >= 2:
                        move_line_pool.reconcile_partial(
                            cr, uid, move_lines, 'auto', context=context)
                if line.reconcile_partial_id:
                    move_lines = [
                        move_line.id for move_line in \
                        line.reconcile_partial_id.line_partial_ids]
                    move_lines.remove(line.id)
                    reconcile_pool.unlink(
                        cr, uid, [
                            line.reconcile_partial_id.id], context=context)
                    if len(move_lines) >= 2:
                        move_line_pool.reconcile_partial(
                            cr, uid, move_lines, 'auto', context=context)
            if voucher.move_id:
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])
        res = {
            'state': 'cancel',
            'move_id': False,
        }
        self.write(cr, uid, ids, res)
        return True


class account_voucher_line(osv.Model):
    _inherit = 'account.voucher.line'

    # Adding support for storno accounting, negative numbers in voucher lines.
    # Amount original is taken from residual amount on accoutn move line, 
    # and amount_unreconciled and amount are calculated with abs.
    # Rewrite check if the residual amount is negative, the unreconciled and 
    # allocated amount will be negative as well.
    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        currency_pool = self.pool.get('res.currency')
        rs_data = {}
        for line in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            ctx.update({'date': line.voucher_id.date})
            voucher_rate = self.pool.get('res.currency').read(
                cr,
                uid,
                line.voucher_id.currency_id.id,
                ['rate'],
                context=ctx)['rate']
            ctx.update({
                'voucher_special_currency': \
                    line.voucher_id.payment_rate_currency_id and \
                    line.voucher_id.payment_rate_currency_id.id or False,
                'voucher_special_currency_rate': \
                    line.voucher_id.payment_rate * voucher_rate})
            res = {}
            company_currency = \
                line.voucher_id.journal_id.company_id.currency_id.id
            voucher_currency = \
                line.voucher_id.currency_id and \
                line.voucher_id.currency_id.id or \
                company_currency
            move_line = line.move_line_id or False

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0
            elif move_line.currency_id and \
                voucher_currency == move_line.currency_id.id:
                res['amount_original'] = move_line.amount_currency
                res['amount_unreconciled'] = move_line.amount_residual_currency
            else:
                # always use the amount booked in the company currency as the
                # basis of the conversion into the voucher currency
                res['amount_original'] = currency_pool.compute(
                    cr,
                    uid,
                    company_currency,
                    voucher_currency,
                    move_line.credit or move_line.debit or 0.0,
                    context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(
                    cr,
                    uid,
                    company_currency,
                    voucher_currency,
                    move_line.amount_residual,
                    context=ctx)

            rs_data[line.id] = res
        return rs_data

    _columns = {
        'amount_original': fields.function(
            _compute_balance,
            multi='dc',
            type='float',
            string='Original Amount',
            store=True,
            digits_compute=dp.get_precision('Account')),
        'amount_unreconciled': fields.function(
            _compute_balance,
            multi='dc',
            type='float',
            string='Open Balance',
            store=True,
            digits_compute=dp.get_precision('Account')),
    }
