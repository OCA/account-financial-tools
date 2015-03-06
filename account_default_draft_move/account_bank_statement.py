# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2012 Camptocamp SA
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
##############################################################################

from openerp.osv import orm


class AccountBankStatement(orm.Model):
    _inherit = "account.bank.statement"

    def create_move_from_st_line(self, cr, uid,
                                 st_line_id, company_currency_id,
                                 st_line_number, context=None):
        move_ids = super(AccountBankStatement, self).create_move_from_st_line(
            cr, uid, st_line_id, company_currency_id,
            st_line_number, context
        )
        # If a bank statement line is already linked to a voucher
        # we received boolean instead of voucher move ids in move_ids
        bank_st_line_obj = self.pool.get('account.bank.statement.line')
        voucher_obj = self.pool.get('account.voucher')
        st_line = bank_st_line_obj.browse(cr, uid, st_line_id, context=context)
        if st_line.voucher_id:
            v = voucher_obj.browse(cr, uid, st_line.voucher_id.id,
                                   context=context)
            move_ids = v.move_id.id

        if not isinstance(move_ids, (tuple, list)):
            move_ids = [move_ids]
        # We receive the move created for the bank statement, we set it
        # to draft
        use_journal_setting = bool(self.pool['ir.config_parameter'].get_param(
            cr, uid, 'use_journal_setting', False))
        if move_ids:
            move_obj = self.pool.get('account.move')
            moves = move_obj.browse(cr, uid, move_ids, context=context)
            for move in moves:
                if use_journal_setting and move.journal_id.entry_posted:
                    continue
                move_obj.write(cr, uid, [move.id],
                               {'state': 'draft'}, context=context)
        return move_ids
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
