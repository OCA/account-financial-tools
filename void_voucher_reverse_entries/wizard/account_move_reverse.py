# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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

from openerp.osv import orm
from openerp.tools.safe_eval import safe_eval


class AccountMoveReverse(orm.TransientModel):
    _name = 'account.move.reverse'
    _inherit = 'account.move.reverse'

    def action_reverse(self, cr, uid, ids, context=None):
        account_move_obj = self.pool['account.move']
        if context is None:
            context = {}

        void_voucher_ids = context.pop("void_voucher_ids", [])
        res = super(AccountMoveReverse, self).action_reverse(cr, uid, ids,
                                                             context=context)
        domain = safe_eval(res["domain"])
        move_ids = domain[0][2]
        if move_ids:
            # Make sure we POST those lines
            account_move_obj.write(cr, uid, move_ids, {'state':'posted'})

        if void_voucher_ids:
            reconcile_ids = set()
            voucher_obj = self.pool["account.voucher"]
            for voucher in voucher_obj.browse(cr, uid, void_voucher_ids,
                                              context=context):
                if voucher.move_ids:
                    for move in voucher.move_ids:
                        if move.reconcile_id:
                            reconcile_ids.add(move.reconcile_id.id)


                if reconcile_ids:
                    self.pool["account.move.reconcile"].unlink(
                        cr, uid, list(reconcile_ids), context=context)

            self.pool.get("account.voucher").write(cr, uid, void_voucher_ids,
                                                   {'state': 'void'},
                                                   context=context)

        return res
