# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2012 Camptocamp SA
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
from datetime import datetime
import operator
from openerp.osv.orm import Model, fields
from openerp.tools.translate import _
from openerp.addons.account_credit_control import run

class AccountAccount(Model):
    """Add a link to a credit control policy on account account"""


    def _check_account_type_compatibility(self, cursor, uid, acc_ids, context=None):
        """We check that account is of type reconcile"""
        if not isinstance(acc_ids, list):
            acc_ids = [acc_ids]
        for acc in self.browse(cursor, uid, acc_ids, context):
            if acc.credit_policy_id and not acc.reconcile:
                return False
        return True

    _inherit = "account.account"
    _description = """Add a link to a credit policy"""
    _columns = {'credit_policy_id': fields.many2one('credit.control.policy',
                                                     'Credit control policy',
                                                     help=("Define global credit policy"
                                                           "order is account partner invoice")),

                'credit_control_line_ids': fields.one2many('credit.control.line',
                                                              'account_id',
                                                              string='Credit Lines',
                                                              readonly=True)}

    _constraints = [(_check_account_type_compatibility,
                     _('You can not set a credit policy on a non reconciliable account'),
                     ['credit_policy_id'])]

class AccountInvoice(Model):
    """Add a link to a credit control policy on account account"""

    _inherit = "account.invoice"
    _description = """Add a link to a credit policy"""
    _columns = {'credit_policy_id': fields.many2one('credit.control.policy',
                                                     'Credit control policy',
                                                     help=("Define global credit policy"
                                                           "order is account partner invoice")),

                'credit_control_line_ids': fields.one2many('credit.control.line',
                                                              'account_id',
                                                              string='Credit Lines',
                                                              readonly=True)}

    def action_move_create(self, cursor, uid, ids, context=None):
        """We ensure writing of invoice id in move line because
           Trigger field may not work without account_voucher addon"""
        res = super(AccountInvoice, self).action_move_create(cursor, uid, ids, context=context)
        for inv in self.browse(cursor, uid, ids, context=context):
            if inv.move_id:
                for line in inv.move_id.line_id:
                    line.write({'invoice_id': inv.id})
        return res


class AccountMoveLine(Model):
    """Add a function that compute the residual amount using a follow up date
       Add relation between move line and invoicex"""

    _inherit = "account.move.line"
    # Store fields has strange behavior with voucher module we had to overwrite invoice


    # def _invoice_id(self, cursor, user, ids, name, arg, context=None):
    #     #Code taken from OpenERP account addon
    #     invoice_obj = self.pool.get('account.invoice')
    #     res = {}
    #     for line_id in ids:
    #         res[line_id] = False
    #     cursor.execute('SELECT l.id, i.id ' \
    #                     'FROM account_move_line l, account_invoice i ' \
    #                     'WHERE l.move_id = i.move_id ' \
    #                     'AND l.id IN %s',
    #                     (tuple(ids),))
    #     invoice_ids = []
    #     for line_id, invoice_id in cursor.fetchall():
    #         res[line_id] = invoice_id
    #         invoice_ids.append(invoice_id)
    #     invoice_names = {False: ''}
    #     for invoice_id, name in invoice_obj.name_get(cursor, user, invoice_ids, context=context):
    #         invoice_names[invoice_id] = name
    #     for line_id in res.keys():
    #         invoice_id = res[line_id]
    #         res[line_id] = (invoice_id, invoice_names[invoice_id])
    #     return res

    # def _get_invoice(self, cursor, uid, ids, context=None):
    #     result = set()
    #     for line in self.pool.get('account.invoice').browse(cursor, uid, ids, context=context):
    #         if line.move_id:
    #             ids = [x.id for x in line.move_id.line_id or []]
    #     return list(result)

    # _columns = {'invoice_id': fields.function(_invoice_id, string='Invoice',
    #             type='many2one', relation='account.invoice',
    #             store={'account.invoice': (_get_invoice, ['move_id'], 20)})}

    _columns = {'invoice_id': fields.many2one('account.invoice', 'Invoice')}

    def _get_payment_and_credit_lines(self, moveline_array, lookup_date):
        credit_lines = []
        payment_lines = []
        for line in moveline_array:
            if self._should_exlude_line(line):
                continue
            if line.account_id.type == 'receivable' and line.debit:
                credit_lines.append(line)
            else:
                if line.reconcile_partial_id:
                    payment_lines.append(line)
        credit_lines.sort(key=operator.attrgetter('date'))
        payment_lines.sort(key=operator.attrgetter('date'))
        return (credit_lines, payment_lines)

    def _validate_line_currencies(self, credit_lines):
        """Raise an excpetion if there is lines with different currency"""
        if len(credit_lines) == 0:
            return True
        currency = credit_lines[0].currency_id.id
        if not all(obj.currency_id.id == currency for obj in credit_lines):
            raise Exception('Not all line of move line are in the same currency')

    def _get_value_amount(self, mv_line_br):
        if mv_line_br.currency_id:
            return mv_line_br.amount_currency
        else:
            return mv_line_br.debit - mv_line_br.credit

    def _validate_partial(self, credit_lines):
        if len(credit_lines) == 0:
            return True
        else:
            line_with_partial = 0
            for line in credit_lines:
                if not line.reconcile_partial_id:
                    line_with_partial += 1
            if line_with_partial and line_with_partial != len(credit_lines):
                    raise Exception('Can not compute credit line if multiple'
                                    ' lines are not all linked to a partial')

    def _get_applicable_payment_lines(self, credit_line, payment_lines):
        applicable_payment = []
        for pay_line in payment_lines:
            if datetime.strptime(pay_line.date, "%Y-%m-%d").date() \
                <= datetime.strptime(credit_line.date, "%Y-%m-%d").date():
                applicable_payment.append(pay_line)
        return applicable_payment

    def _compute_partial_reconcile_residual(self, move_lines, lookup_date, move_id, memoizer):
        """ Compute open amount of multiple credit lines linked to multiple payment lines"""
        credit_lines, payment_lines = self._get_payment_and_credit_lines(move_lines, lookup_date, memoizer)
        self._validate_line_currencies(credit_lines)
        self._validate_line_currencies(payment_lines)
        self._validate_partial(credit_lines)
        # memoizer structure move_id : {move_line_id: open_amount}
        # paymnent line and credit line are sorted by date
        rest = 0.0
        for credit_line in credit_lines:
            applicable_payment = self._get_applicable_payment_lines(credit_line, payment_lines)
            paid_amount = 0.0
            for pay_line in applicable_payment:
                paid_amount += self._get_value_amount(pay_line)
            balance_amount = self._get_value_amount(credit_lines) - (paid_amount + rest)
            memoizer[move_id][credit_line.id] = balance_amount
            if balance_amount < 0.0:
                rest = balance_amount
            else:
                rest = 0.0
        return memoizer

    def _compute_fully_open_amount(self, move_lines, lookup_date, move_id, memoizer):
        for move_line in move_lines:
            memoizer[move_id][move_line.id] = self._get_value_amount(move_line)
        return memoizer


    def _amount_residual_from_date(self, cursor, uid, mv_line_br, lookup_date, context=None):
        """
        Code from function _amount_residual of account/account_move_line.py does not take
        in account mulitple line payment and reconciliation. We have to rewrite it
        Code computes residual amount at lookup date for mv_line_br in entry
        """
        memoizer = run.memoizers['credit_line_residuals']
        move_id = mv_line_br.move_id.id
        if mv_line_br.move_id.id in memoizer:
            pass # get back value
        else:
            memoizer[move_id] = {}
            move_lines = mv_line_br.move_id.line_id
            if mv_line_br.reconcile_partial_id:
                self._compute_partial_reconcile_residual(move_lines, lookup_date, move_id, memoizer)
            else:
                self._compute_fully_open_amount(move_lines, lookup_date, move_id, memoizer)
        return memoizer[move_id][mv_line_br.id]

