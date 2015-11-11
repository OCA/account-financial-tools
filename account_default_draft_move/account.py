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

from openerp.osv import orm, osv, fields
from tools.translate import _


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def action_move_create(self, cr, uid, ids, context=None):
        """Set move line in draft state after creating them."""
        res = super(AccountInvoice, self).action_move_create(cr, uid, ids,
                                                             context=context)
        move_obj = self.pool.get('account.move')
        use_journal_setting = bool(self.pool['ir.config_parameter'].get_param(
            cr, uid, 'use_journal_setting', False))
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.move_id:
                if use_journal_setting and inv.move_id.journal_id.entry_posted:
                    continue
                move_obj.write(cr, uid, [inv.move_id.id], {'state': 'draft'},
                               context=context)
        return res


class AccountMove(orm.Model):
    _inherit = 'account.move'

    def _is_update_posted(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        ir_module = self.pool['ir.module.module']
        if ir_module.search(cr, uid, [('name', '=', 'account_cancel'),
                                      ('state', '=', 'installed')]):
            for move in self.browse(cr, uid, ids, context=context):
                res[move.id] = move.journal_id.update_posted
        return res

    _columns = {
        'update_posted': fields.function(
            _is_update_posted, method=True, type='boolean',
            string='Allow Cancelling Entries'),
    }

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


class AccountJournal(orm.Model):
    _inherit = 'account.journal'

    def __init__(self, pool, cr):
        super(AccountJournal, self).__init__(pool, cr)
        # update help of entry_posted flag
        self._columns['entry_posted'].string = 'Skip \'Draft\' State'
        self._columns['entry_posted'].help = \
            """Check this box if you don't want new journal entries
to pass through the 'draft' state and instead goes directly
to the 'posted state' without any manual validation."""
        return
