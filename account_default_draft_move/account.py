# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville/Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
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

from openerp.osv import fields, orm, osv
from tools.translate import _


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'
    
    def action_move_create(self, cr, uid, ids, context=None):
        """Set move line in draft state after creating them."""
        res = super(AccountInvoice,self).action_move_create(cr, uid, ids, context=context)
        move_obj = self.pool.get('account.move')
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.move_id:
                move_obj.write(cr, uid, [inv.move_id.id], {'state': 'draft'}, context=context)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
