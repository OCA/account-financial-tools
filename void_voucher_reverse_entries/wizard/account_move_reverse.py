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


class AccountMoveReverse(orm.TransientModel):
    _name = 'account.move.reverse'
    _inherit = 'account.move.reverse'

    def action_reverse(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        void_voucher_ids = context.pop("void_voucher_ids", [])
        res = super(AccountMoveReverse, self).action_reverse(cr, uid, ids,
                                                             context=context)
        if void_voucher_ids:
            self.pool.get("account.voucher").write(cr, uid, void_voucher_ids,
                                                   {'state': 'void'},
                                                   context=context)

        return res
