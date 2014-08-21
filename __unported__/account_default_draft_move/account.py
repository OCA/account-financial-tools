# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville/Joel Grand-Guillaume.
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
##############################################################################

from openerp.osv import orm, osv
from tools.translate import _


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def action_move_create(self, cr, uid, ids, context=None):
        """Set move line in draft state after creating them."""
        res = super(AccountInvoice, self).action_move_create(cr, uid, ids,
                                                             context=context)
        move_obj = self.pool.get('account.move')
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.move_id:
                move_obj.write(cr, uid, [inv.move_id.id], {'state': 'draft'},
                               context=context)
        return res


class AccountMove(orm.Model):
    _inherit = 'account.move'

    def button_cancel(self, cr, uid, ids, context=None):
        """ We rewrite function button_cancel, to allow invoice or bank
        statement with linked draft moved
        to be canceled

        """
        for line in self.browse(cr, uid, ids, context=context):
            if line.state == 'draft':
                continue
            else:
                if not line.journal_id.update_posted:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You cannot modify a posted entry of this journal.'
                          'First you should set the journal '
                          'to allow cancelling entries.')
                    )
        if ids:
            cr.execute('UPDATE account_move '
                       'SET state=%s '
                       'WHERE id IN %s', ('draft', tuple(ids),))
        return True
