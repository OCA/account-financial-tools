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

from openerp.osv import orm, fields


class AccountVoucher(orm.Model):
    _inherit = 'account.voucher'
    _name = 'account.voucher'

    _columns = {
        'state': fields.selection(
            [('draft', 'Draft'),
             ('cancel', 'Cancelled'),
             ('proforma', 'Pro-forma'),
             ('posted', 'Posted'),
             ('void', 'Void'),
             ],
            'Status', readonly=True, size=32, track_visibility='onchange',
            help="""
* The 'Draft' status is used when a user is encoding a new and unconfirmed Voucher.
* The 'Pro-forma' when voucher is in Pro-forma status,voucher does not have an voucher number.
* The 'Posted' status is used when user create voucher,a voucher number is generated and voucher entries are created in account
* The 'Cancelled' status is used when user cancel voucher.
* The 'Void' status has been reversed by another entry.""",
        )
    }

    def action_void_reverse(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        move_ids = list(set(
            move_line.move_id.id
            for move_line in self.browse(
                cr, uid, ids[0], context=context,
            ).move_ids
            if move_line.move_id
        ))

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.move.reverse',
            'target': 'new',
            'context': dict(context,
                            active_ids=move_ids,
                            void_voucher_ids=ids[:1]),
        }
