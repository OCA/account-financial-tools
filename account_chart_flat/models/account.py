# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Chart Flat, for OpenERP 7.0 / Odoo 8
#    Copyright (C) 2013 XCG Consulting <http://odoo.consulting>
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

from openerp.osv import osv
from openerp.osv import fields
import openerp.addons.decimal_precision as dp
from openerp.addons.account.account import account_account


class FlatAccount(osv.Model):
    _name = 'account.account'
    _inherit = 'account.account'

    _parent_store = False

    def create(self, cr, uid, values, context=None):
        """override the create method of account.account to make sure we
        send the magic context in order to avoid recalculation the COA
        structure on every account creation
        """

        if not context:
            context = {}

        context.update(
            {
                'defer_parent_store_computation': True
            }
        )
        return super(FlatAccount, self).create(
            cr, uid, values, context=context
        )

    def write(self, cr, uid, ids, values, context=None):
        """override the create method of account.account to make sure we
        send the magic context in order to avoid recalculation the COA
        structure on every account modification
        """

        if not context:
            context = {}

        context.update(
            {
                'defer_parent_store_computation': True
            }
        )
        return super(FlatAccount, self).write(
            cr, uid, ids, values, context=context
        )

    def __compute(
        self, cr, uid, ids, field_names, arg=None, context=None,
        query='', query_params=()
    ):
        null_result = dict((fn, 0.0) for fn in field_names)
        intermediate_result = dict((id_, null_result) for id_ in ids)

        # TODO: we will reactivate this when we reconfigure compute to
        # block the:
        # ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)],
        #                    context=context)
        # Because child_of makes use of the parent_left and parent_right
        # which is missing and will provoke: IndexError: pop from empty list
        # down the road...

        # search_args = [
        #     '&',
        #     ('id', 'in', ids),
        #     ('type', 'not in', ['consolidation', 'view'])
        # ]
        # real_ids = self.search(cr, uid, search_args, context=context)
        # real_results = account_account._account_account__compute(
        #     self, cr, uid, real_ids, field_names, arg=arg, context=context,
        #     query=query, query_params=query_params
        # )
        # intermediate_result.update(real_results)

        return intermediate_result

    _columns = {
        # Override the following fields to change the function they point to.
        # (See account/account.py for the original code.)
        'balance': fields.function(
            __compute,
            digits_compute=dp.get_precision('Account'),
            string=u"Balance",
            multi='balance',
        ),
        'credit': fields.function(
            __compute,
            fnct_inv=account_account._set_credit_debit,
            digits_compute=dp.get_precision('Account'),
            string=u"Credit",
            multi='balance',
        ),
        'debit': fields.function(
            __compute,
            fnct_inv=account_account._set_credit_debit,
            digits_compute=dp.get_precision('Account'),
            string=u"Debit",
            multi='balance',
        ),
        'foreign_balance': fields.function(
            __compute,
            digits_compute=dp.get_precision('Account'),
            string=u"Foreign Balance",
            multi='balance',
            help=(
                u"Total amount (in Secondary currency) for transactions held "
                u"in secondary currency for this account."
            ),
        ),
        'adjusted_balance': fields.function(
            __compute,
            digits_compute=dp.get_precision('Account'),
            string=u"Adjusted Balance",
            multi='balance',
            help=(
                u"Total amount (in Company currency) for transactions held in "
                u"secondary currency for this account."
            ),
        ),
        'unrealized_gain_loss': fields.function(
            __compute,
            digits_compute=dp.get_precision('Account'),
            string=u"Unrealized Gain or Loss",
            multi='balance',
            help=(
                u"Value of Loss or Gain due to changes in exchange rate when "
                u"doing multi-currency transactions."
            ),
        ),
    }
