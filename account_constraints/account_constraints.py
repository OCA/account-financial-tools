# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.osv import fields, osv
from openerp.tools.translate import _

class AccountAccount(osv.osv):
    _inherit = 'account.account'

    # Forbid to change type of account for 'consolidation' and 'view' if there is entries on it or his children.
    def _check_allow_type_change(self, cr, uid, ids, new_type, context=None):
        restricted_groups = ['consolidation','view']
        line_obj = self.pool.get('account.move.line')
        for account in self.browse(cr, uid, ids, context=context):
            old_type = account.type
            account_ids = self.search(cr, uid, [('id', 'child_of', [account.id])])
            if line_obj.search(cr, uid, [('account_id', 'in', account_ids)]):
                #Check for 'Closed' type
                if old_type == 'closed' and new_type !='closed':
                    raise osv.except_osv(
                        _('Warning !'), 
                        _("You cannot change the type of account from 'Closed' to any other type as it contains journal items!")
                    )
                # Forbid to change an account type for restricted_groups as it contains journal items (or if one of its children does)
                if (new_type in restricted_groups):
                    raise osv.except_osv(
                        _('Warning !'), 
                        _("You cannot change the type of account to '%s' type as it contains journal items!") % (new_type,)
                    )

        return True

    # For legal reason (forbiden to modify journal entries which belongs to a closed fy or period), Forbid to modify
    # the code of an account if journal entries have been already posted on this account. This cannot be simply 
    # 'configurable' since it can lead to a lack of confidence in OpenERP and this is what we want to change.
    def _check_allow_code_change(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.move.line')
        for account in self.browse(cr, uid, ids, context=context):
            account_ids = self.search(cr, uid, [('id', 'child_of', [account.id])], context=context)
            if line_obj.search(cr, uid, [('account_id', 'in', account_ids)], context=context):
                raise osv.except_osv(_('Warning !'), _("You cannot change the code of account which contains journal items!"))
        return True

    # Add a check to forbid as well to change the code of an account which have entries !
    def write(self, cr, uid, ids, vals, context=None):
        res = super(AccountAccount, self).write(cr, uid, ids, vals, context=context)
        if 'code' in vals.keys():
            self._check_allow_code_change(cr, uid, ids, context=context)
        return res


class AccountMove(osv.osv):
    _inherit = "account.move"

    def _check_fiscal_year(self, cursor, user, ids):
        for move in self.browse(cursor, user, ids):
            date_start = move.period_id.fiscalyear_id.date_start
            date_stop = move.period_id.fiscalyear_id.date_stop
            if move.date < date_start or move.date > date_stop:
                return False
        return True

    _constraints = [
        (_check_fiscal_year,
            'You cannot create entries with date not in the fiscal year of the chosen period',
            ['line_id','']),
    ]

    def unlink(self, cr, uid, ids, context={}, check=True):
        for move in self.browse(cr, uid, ids, context):
            for line in move.line_id:
                if line.invoice:
                    raise osv.except_osv(_('User Error!'),
                            _("Move cannot be deleted if linked to an invoice. (Invoice: %s - Move ID:%s)") % \
                                    (line.invoice.number,move.name))
        result = super(AccountMove, self).unlink(cr, uid, ids, context)
        return result


class AccountMoveReconcile(osv.osv):
    _inherit = "account.move.reconcile"


    # Look in the line_id and line_partial_ids to ensure the partner is the same or empty
    # on all lines. We allow that only for opening/closing period
    def _check_same_partner(self, cr, uid, ids, context=None):
        for reconcile in self.browse(cr, uid, ids, context=context):
            move_lines = []
            if not reconcile.opening_reconciliation:
                if reconcile.line_id:
                    first_partner = reconcile.line_id[0].partner_id.id
                    move_lines = reconcile.line_id
                elif reconcile.line_partial_ids:
                    first_partner = reconcile.line_partial_ids[0].partner_id.id
                    move_lines = reconcile.line_partial_ids
                if any([line.partner_id.id != first_partner for line in move_lines]):
                    return False
        return True

    _constraints = [
        (_check_same_partner, 'You can only reconcile journal items with the same partner.', ['line_id']),
    ]

    _columns = {
        'opening_reconciliation': fields.boolean(
                'Opening Entries Reconciliation', 
                help="Is this reconciliation produced by the opening of a new fiscal year ?."
            ),
    }
    
    # You cannot unlink a reconciliation if it is a opening_reconciliation one,
    # you should use the generate opening entries wizard for that
    def unlink(self, cr, uid, ids, context=None):
        for move_rec in self.browse(cr, uid, ids, context=context):
            if move_rec.opening_reconciliation:
                raise osv.except_osv(_('Error!'), _('You cannot unreconcile journal items if they has been generated by the \
                                                        opening/closing fiscal year process.'))
        return super(AccountMoveReconcile, self).unlink(cr, uid, ids, context=context)


class AccountBankSatement(osv.osv):
    _inherit = "account.bank.statement"

    def write(self, cr, uid, ids, vals, context=None):
        # Restrict to modify the journal if we already have some voucher of reconciliation created/generated.
        # Because the voucher keeps in memory the journal it was created with.
        for bk_st in self.browse(cr, uid, ids, context=context):
            if vals.get('journal_id') and bk_st.line_ids:
                if any([x.voucher_id and True or False for x in bk_st.line_ids]):
                    raise osv.except_osv(
                        _('Unable to change journal !'), 
                        _('You can not change the journal as you already reconciled some statement lines!')
                    )
        return super(AccountBankSatement, self).write(cr, uid, ids, vals, context=context)

AccountBankSatement()


class AccountMoveLine(osv.osv):
    _inherit='account.move.line'
    
    def _check_currency_and_amount(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if (l.currency_id and not l.amount_currency) or (not l.currency_id and l.amount_currency):
                return False
        return True

    def _check_currency_amount(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if l.amount_currency:
                if (l.amount_currency > 0.0 and l.credit > 0.0) or (l.amount_currency < 0.0 and l.debit > 0.0):
                    return False
        return True

    def _check_currency_company(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if l.currency_id.id == l.company_id.currency_id.id:
                return False
        return True

    _constraints = [
            (
                _check_currency_and_amount, 
                "You cannot create journal items with a secondary currency without recording \
                    both 'currency' and 'amount currency' field.",
                ['currency_id','amount_currency']
            ),
            (
                _check_currency_amount, 
                'The amount expressed in the secondary currency must be positif when journal item\
                 are debit and negatif when journal item are credit.', 
                 ['amount_currency']
            ),
            (
                _check_currency_company, 
                "You can't provide a secondary currency if the same than the company one." , 
                ['currency_id']
            ),
        ]
        

class Invoice(osv.osv):
    _inherit = 'account.invoice'

    # Forbid to cancel an invoice if the related move lines have already been
    # used in a payment order. The risk is that importing the payment line
    # in the bank statement will result in a crash cause no more move will
    # be found in the payment line
    def action_cancel(self, cr, uid, ids, *args):
        payment_line_obj = self.pool.get('payment.line')
        for inv in self.browse(cr, uid, ids, *args):
            pl_line_ids = False
            if inv.move_id and inv.move_id.line_id:
                inv_mv_lines = [x.id for x in inv.move_id.line_id]
                pl_line_ids = payment_line_obj.search(cr, uid, [('move_line_id','in',inv_mv_lines)], *args)
            if pl_line_ids:
                pay_line = payment_line_obj.browse(cr, uid, pl_line_ids, *args)
                payment_order_name = ','.join(map(lambda x: x.order_id.reference, pay_line))
                raise osv.except_osv(
                    _('Error!'), 
                    _("You cannot cancel an invoice which has already been imported in a payment order. \
                        Remove it from the following payment order : %s."%(payment_order_name))
                )
        return super(Invoice, self).action_cancel(cr, uid, ids, *args)

