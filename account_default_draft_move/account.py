# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Camptocamp (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Vincent Renaville (Camptocamp)
#

# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
from tools.translate import _

class account_move(osv.osv):
    _inherit = "account.move"
    
    def post(self, cr, uid, ids, context=None):
        return_value = super(account_move,self).post(cr, uid, ids, context)
        if return_value:
            invoice = context.get('invoice', False)
            ## We test that we have an invoice in the context, in this case move net to be set to draft
            ## in this condition we can cancel a invoice
            if invoice:
                valid_moves = self.validate(cr, uid, ids, context)
                if not valid_moves:
                    raise osv.except_osv(_('Integrity Error !'), _('You can not validate a non-balanced entry !\nMake sure you have configured payment terms properly !\nThe latest payment term line should be of the type "Balance" !'))
                cr.execute('UPDATE account_move '\
                           'SET state=%s '\
                           'WHERE id IN %s',
                           ('draft', tuple(valid_moves),))
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.period_id.state == 'done':
                raise osv.except_osv(_('Error !'), _('You can not modify a posted entry of closed periods'))
            ## Change the test of line state instead of journal type
            elif line.state == 'posted':
                raise osv.except_osv(_('Error !'), _('You can not modify a posted entry of this journal !\nYou should set the journal to allow cancelling entries if you want to do that.'))
        if ids:
            cr.execute('UPDATE account_move '\
                       'SET state=%s '\
                       'WHERE id IN %s', ('draft', tuple(ids),))
        return True

    
account_move()