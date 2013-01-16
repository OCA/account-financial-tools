# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
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

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


class AccountAccount(orm.Model):
    _inherit = 'account.account'

    # Forbid to change type of account for 'consolidation' and 'view' if
    # there are entries on it or its children.
    def _check_allow_type_change(self, cr, uid, ids, new_type, context=None):
        restricted_groups = ['consolidation', 'view']
        line_obj = self.pool.get('account.move.line')
        for account in self.browse(cr, uid, ids, context=context):
            old_type = account.type
            account_ids = self.search(cr, uid,
                                      [('id', 'child_of', [account.id])],
                                      context=context)
            if line_obj.search(cr, uid,
                               [('account_id', 'in', account_ids)],
                               context=context):
                # Check for 'Closed' type
                if old_type == 'closed' and new_type != 'closed':
                    raise osv.except_osv(
                        _('Warning'),
                        _("You cannot change the type of account from 'Closed'"
                          " to any other type as it contains journal items.")
                    )
                # Forbid to change an account type for restricted_groups
                # as it contains journal items (or if one of its
                # children does)
                if (new_type in restricted_groups):
                    raise osv.except_osv(
                        _('Warning  '),
                        _("You cannot change the type of account to '%s' type "
                          "as it contains journal items.") % new_type
                    )

        return True

    # For legal reason (forbidden to modify journal entries which belongs
    # to a closed fy or period), forbid to modify the code of an account
    # if journal entries have been already posted on this account. This
    # cannot be simply 'configurable' since it can lead to a lack of
    # confidence in OpenERP and this is what we want to change.
    def _check_allow_code_change(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.move.line')
        for account in self.browse(cr, uid, ids, context=context):
            account_ids = self.search(cr, uid,
                                      [('id', 'child_of', [account.id])],
                                      context=context)
            if line_obj.search(cr, uid,
                               [('account_id', 'in', account_ids)],
                               context=context):
                raise osv.except_osv(
                    _('Warning'),
                    _("You cannot change the code of an account "
                      "which contains journal items.")
                )
        return True

    # Add a check to forbid as well to change the code of an account
    # which have entries !
    def write(self, cr, uid, ids, vals, context=None):
        res = super(AccountAccount, self).write(
                cr, uid, ids, vals, context=context)
        if 'code' in vals:
            self._check_allow_code_change(cr, uid, ids, context=context)
        return res


class AccountMoveLine(orm.Model):
    _inherit = "account.move.line"

    def _remove_move_reconcile(self, cr, uid, move_ids=None,
                               opening_reconciliation=False, context=None):
        """Redefine the whole method to add the kwarg opening_reconciliation."""
        # Function remove move reconcile ids related with moves
        obj_move_line = self.pool.get('account.move.line')
        obj_move_rec = self.pool.get('account.move.reconcile')
        unlink_ids = []
        if not move_ids:
            return True
        recs = obj_move_line.read(cr, uid, move_ids,
                                  ['reconcile_id', 'reconcile_partial_id'],
                                  context=context)
        rec_ids = [rec['reconcile_id'][0]
                   for rec in recs
                   if rec['reconcile_id']]
        part_rec_ids = [rec['reconcile_partial_id'][0]
                        for rec in recs
                        if rec['reconcile_partial_id']]
        unlink_ids += rec_ids
        unlink_ids += part_rec_ids
        if unlink_ids:
            if opening_reconciliation:
                obj_move_rec.write(cr, uid, unlink_ids,
                                   {'opening_reconciliation': False},
                                   context=context)
            obj_move_rec.unlink(cr, uid, unlink_ids, context=context)
        return True

    def _check_currency_amount(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if l.amount_currency:
                if ((l.amount_currency > 0.0 and l.credit > 0.0) or
                        (l.amount_currency < 0.0 and l.debit > 0.0)):
                    return False
        return True

    _constraints = [
            (_check_currency_amount,
             "The amount expressed in the secondary currency must be positive "
             "when journal items are debit and negative when journal items "
             "are credit.",
             ['amount_currency']
            ),
        ]


class AccountMove(orm.Model):
    _inherit = "account.move"

    def _check_fiscal_year(self, cr, user, ids):
        for move in self.browse(cr, user, ids):
            date_start = move.period_id.fiscalyear_id.date_start
            date_stop = move.period_id.fiscalyear_id.date_stop
            if not date_start <= move.date <= date_stop:
                return False
        return True

    _constraints = [
        (_check_fiscal_year,
         'You cannot create entries with date not in the fiscal year '
         'of the chosen period.',
         ['line_id']),
    ]

    def unlink(self, cr, uid, ids, context=None, check=True):
        for move in self.browse(cr, uid, ids, context):
            for line in move.line_id:
                if line.invoice:
                    raise osv.except_osv(
                            _('User Error'),
                            _("Move cannot be deleted if linked to an invoice."
                              " (Invoice: %s - Move ID:%s)") %
                              (line.invoice.number, move.name))
        return super(AccountMove, self).unlink(cr, uid, ids, context)


class AccountMoveReconcile(orm.Model):
    _inherit = "account.move.reconcile"

    # Look in the line_id and line_partial_ids to ensure the partner is
    # the same or empty on all lines. We allow that only for
    # opening/closing period
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
        (_check_same_partner,
         'You can only reconcile journal items with '
         'the same partner.',
         ['line_id']),
    ]

    _columns = {
        'opening_reconciliation': fields.boolean(
                'Opening Entries Reconciliation',
                help="Is this reconciliation produced by the opening of "
                     "a new fiscal year?"
            ),
    }

    # You cannot unlink a reconciliation if it is a
    # opening_reconciliation one, you should use the generate opening
    # entries wizard for that
    def unlink(self, cr, uid, ids, context=None):
        for move_rec in self.browse(cr, uid, ids, context=context):
            if move_rec.opening_reconciliation:
                raise osv.except_osv(
                            _('Error'),
                            _("You cannot unreconcile journal items if they "
                              "have been generated by the opening/closing "
                              "fiscal year process.")
                        )
        return super(AccountMoveReconcile, self).unlink(cr, uid, ids, context=context)


class AccountBankSatement(orm.Model):
    _inherit = "account.bank.statement"

    def write(self, cr, uid, ids, vals, context=None):
        # Restrict to modify the journal if we already have some voucher
        # of reconciliation created/generated.  Because the voucher
        # keeps in memory the journal it was created with.
        for bk_st in self.browse(cr, uid, ids, context=context):
            if vals.get('journal_id') and bk_st.line_ids:
                if any([x.voucher_id and True or False for x in bk_st.line_ids]):
                    raise osv.except_osv(
                        _('Unable to change journal'),
                        _('You can not change the journal as you already '
                          'reconciled some statement lines.')
                    )
        return super(AccountBankSatement, self).write(cr, uid, ids, vals, context=context)


class Invoice(orm.Model):
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
                pl_line_ids = payment_line_obj.search(
                        cr, uid, [('move_line_id', 'in', inv_mv_lines)], *args)
            if pl_line_ids:
                pay_line = payment_line_obj.browse(cr, uid, pl_line_ids, *args)
                payment_order_name = ','.join([x.order_id.reference for x in pay_line])
                raise osv.except_osv(
                    _('Error'),
                    _("You cannot cancel an invoice which has already been "
                      "imported in a payment order. Remove it from the "
                      "following payment order : %s." % payment_order_name)
                )
        return super(Invoice, self).action_cancel(cr, uid, ids, *args)
