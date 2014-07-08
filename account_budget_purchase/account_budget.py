# -*- coding: utf-8 -*-
##############################################################################
#
#    This module is copyright (C) 2014 Numérigraphe SARL. All Rights Reserved.
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

from openerp.osv import orm, fields


class AccountBudgetPosition (orm.Model):
    """Add purchase orders to budget positions"""
    _inherit = 'account.budget.post'

    _columns = {
        'include_purchase': fields.boolean(
            'Include Purchase Orders',
            help="Check this box to take Purchase orders into account.\n"
                 "If unchecked, only the Accounting Entries will be "
                 "taken into account.\n"
                 "This field lets managers make more realistic Budgets "
                 "when dealing with suppliers who send their invoices late "
                 "(i.e. monthly invoices after reception).\n"
        ),
        # The values are immutable on purpose: they trigger different code
        'purchase_sign': fields.selection(
            (('+', 'Positive'), ('-', 'Negative')), "Sign",
            help="If you select 'Positive', the sum of all the "
                 "lines of Purchase Orders already confirmed but not yet "
                 "Invoiced will be added to the 'real amount' of all the "
                 "Budget Lines that use this Budgetary position.\n"
                 "If you select 'Negative', it will be subtracted "
                 "instead.\n"
        ),
    }


class BudgetLine(orm.Model):
    """Adapt the computation of the Real amount"""

    _inherit = "crossovered.budget.lines"

    # Only count the PO with the following states
    PO_STATES = [
        'confirmed',
        'approved',
        'except_picking',
        'except_invoice',
        'done',
    ]

    # Doing this on _prac would need us to redefine the field too
    def _prac_amt(self, cr, uid, ids, context=None):
        """Optionally add/subtract the amount of the Purchase Order Lines"""
        # Get the standard amounts
        results = super(BudgetLine, self)._prac_amt(cr, uid, ids,
                                                    context=context)
        # Compute the total amount of current purchase order lines
        po_obj = self.pool["purchase.order"]
        po_ids = po_obj.search(
            cr, uid, [('state', 'in', self.PO_STATES)], context=context)
        # XXX does it need rounding?
        po_amount = sum([po.amount_untaxed * (100.0 - po.invoiced_rate) / 100.0
                         for po in po_obj.browse(cr, uid, po_ids,
                                                 context=context)
                         if not po.invoiced])
        if not po_amount:
            # Nothing to do if no POs are running
            return results
        # Add/subtract the total amount of POs to/from lines
        for line in self.browse(cr, uid, ids, context=context):
            if line.general_budget_id.include_purchase:
                if line.general_budget_id.purchase_sign == '+':
                    results[line.id] += po_amount
                elif line.general_budget_id.purchase_sign == '-':
                    results[line.id] -= po_amount
        return results
