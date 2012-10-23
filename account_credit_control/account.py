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
import operator
from datetime import datetime

from openerp.osv.orm import Model, fields
from openerp.tools.translate import _
from openerp.addons.account_credit_control import run


class AccountAccount(Model):
    """Add a link to a credit control policy on account.account"""

    _inherit = "account.account"

    def _check_account_type_compatibility(self, cursor, uid, acc_ids, context=None):
        """We check that account is of type reconcile"""
        if isinstance(acc_ids, (int, long)):
            acc_ids = [acc_ids]
        for acc in self.browse(cursor, uid, acc_ids, context):
            if acc.credit_policy_id and not acc.reconcile:
                return False
        return True

    _columns = {
        'credit_policy_id': fields.many2one('credit.control.policy',
                                            'Credit Control Policy',
                                             help=("The Credit Control Policy "
                                                   "used for this account. This "
                                                   "setting can be forced on the "
                                                   "partner or the invoice.")),

        'credit_control_line_ids': fields.one2many('credit.control.line',
                                                   'account_id',
                                                   string='Credit Lines',
                                                   readonly=True)
    }

    _constraints = [(_check_account_type_compatibility,
                     _('You can not set a credit control policy on a non reconcilable account'),
                    ['credit_policy_id'])]


class AccountInvoice(Model):
    """Add a link to a credit control policy on account.account"""

    _inherit = "account.invoice"
    _columns = {
        'credit_policy_id': fields.many2one('credit.control.policy',
                                            'Credit Control Policy',
                                             help=("The Credit Control Policy "
                                                   "used for this invoice. "
                                                   "If nothing is defined, "
                                                   "it will use the account "
                                                   "setting or the partner "
                                                   "setting.")),

        'credit_control_line_ids': fields.one2many('credit.control.line',
                                                   'account_id',
                                                   string='Credit Lines',
                                                   readonly=True)
    }

    def action_move_create(self, cursor, uid, ids, context=None):
        """ Write the id of the invoice in the generated moves. """
        res = super(AccountInvoice, self).action_move_create(cursor, uid, ids, context=context)
        for inv in self.browse(cursor, uid, ids, context=context):
            if inv.move_id:
                for line in inv.move_id.line_id:
                    line.write({'invoice_id': inv.id})
        return res


class AccountMoveLine(Model):
    """Add a method which computes the residual amount using a follow up date.
       Add relation between move line and invoice."""

    _inherit = "account.move.line"

    _columns = {'invoice_id': fields.many2one('account.invoice', 'Invoice')}

    def _get_payment_and_debit_lines(self, move_lines):
        """ Split the move lines of a move between debit and payment lines.
        Lines partially reconciled are considered as payments.

        Ignore the other move lines.

        Returns them in a tuple, ordered by date

        :param list move_lines: move lines to sort
        :return: tuple where 1st item is a list of the debit lines ordered by date
                 and 2nd item is a list of the payment lines order by date
        """
        debit_lines = []
        payment_lines = []
        for line in move_lines:
            if line.account_id.type == 'receivable' and line.debit:
                debit_lines.append(line)
            else:
                if line.reconcile_partial_id:
                    payment_lines.append(line)
        debit_lines.sort(key=operator.attrgetter('date'))
        payment_lines.sort(key=operator.attrgetter('date'))
        return (debit_lines, payment_lines)

    def _validate_line_currencies(self, move_lines):
        """Raise an exception if there is lines with different currency"""
        if len(move_lines) == 0:
            return True
        currency_id = move_lines[0].currency_id.id
        if not all(obj.currency_id.id == currency_id for obj in move_lines):
            # FIXME: Exception is too large
            raise Exception('Not all line of move line are in the same currency')

    def _get_value_amount(self, move_lines):
        """ For a move line, returns the balance
        Use the amount currency if there is a currency on the move line.
        """
        if move_lines.currency_id:
            return move_lines.amount_currency
        else:
            return move_lines.debit - move_lines.credit

    def _validate_partial(self, move_lines):
        """ Check if all the credit lines are partially reconciled """
        if len(move_lines) == 0:
            return True
        else:
            line_with_partial = 0
            for line in move_lines:
                if not line.reconcile_partial_id:
                    line_with_partial += 1
            if line_with_partial and line_with_partial != len(move_lines):
                # FIXME: Exception is too large
                raise Exception('Can not compute credit line if multiple'
                                ' lines are not all linked to a partial')

    def _get_applicable_payment_lines(self, debit_line, payment_lines):
        """ 
        """
        applicable_payment = []
        for pay_line in payment_lines:
            if datetime.strptime(pay_line.date, "%Y-%m-%d").date() \
                <= datetime.strptime(debit_line.date, "%Y-%m-%d").date():
                applicable_payment.append(pay_line)
        return applicable_payment

    def _compute_partial_reconcile_residual(self, move_lines):
        """ Compute open amount of multiple debit lines
        which have at least one payment.

        :return: dict with each move line id and its residual
        """
        debit_lines, payment_lines = self._get_payment_and_debit_lines(move_lines)
        self._validate_line_currencies(debit_lines)
        self._validate_line_currencies(payment_lines)
        self._validate_partial(debit_lines)

        # payment lines and credit lines are sorted by date
        rest = 0.0
        residuals = {}
        for debit_line in debit_lines:
            applicable_payment = self._get_applicable_payment_lines(debit_line, payment_lines)
            paid_amount = 0.0
            for pay_line in applicable_payment:
                paid_amount += self._get_value_amount(pay_line)
            balance_amount = self._get_value_amount(debit_lines) - (paid_amount + rest)
            residuals[debit_line.id] = balance_amount
            if balance_amount < 0.0:
                rest = balance_amount
            else:
                rest = 0.0
        return residuals

    def _compute_fully_open_amount(self, move_lines):
        """ For each move line, returns the full open balance (does not consider
        partial reconcilation)
        :return: dict of move line ids and their open balance
        """
        res = {}
        for move_line in move_lines:
            res[move_line.id] = self._get_value_amount(move_line)
        return res

    def _amount_residual_from_date(self, cursor, uid, move_line, controlling_date, context=None):
        """ Compute the residual amount for a move line.

        Warning: this method uses a global memoizer in run.memoizers.
        Race conditions are actually avoided with a lock in
        ``run.CreditControlRun.generate_credit_lines``
        So, please use this method with caution, do always use a lock.

        :param browse_record move_line: browse records of move line
        :param date controlling_date: date of the credit control
        :return: open balance of the move move line
        """
        memoizer = run.memoizers['credit_line_residuals']
        move_id = move_line.move_id.id
        if move_line.move_id.id not in memoizer:
            memoizer[move_id] = {}
            move_lines = move_line.move_id.line_id  # thanks openerp for the name
                                                    # but that's a one2many
            if move_line.reconcile_partial_id:
                memoizer[move_id].update(
                    self._compute_partial_reconcile_residual(move_lines))
            else:
                memoizer[move_id].update(
                    self._compute_fully_open_amount(move_lines))
        return memoizer[move_id][move_line.id]

