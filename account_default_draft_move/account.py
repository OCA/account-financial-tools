# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Camptocamp (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Vincent Renaville (Camptocamp)
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


from openerp.osv.orm import  TransientModel, fields
from tools.translate import _

class account_move(TransientModel):
    _inherit = "account.move"
    
    def post(self, cr, uid, ids, context=None):
        return_value = super(account_move,self).post(cr, uid, ids, context)
        if return_value:
            invoice = context.get('invoice', False)
            ## We test if the move is related to an invoice in order to post it with draft status
            if invoice:
                valid_moves = self.validate(cr, uid, ids, context)
                if not valid_moves:
                    raise osv.except_osv(_('Integrity Error !'), _('''You can not validate a non-balanced entry!\n \
                    Make sure you have configured payment terms properly!\n \
                    The latest payment term line should be of the type "Balance" !'''))
                move_obj = self.pool.get('account.move')
                move_obj.write(cr, uid, valid_moves, {'state': 'draft'}, context=context)

                cr.execute('UPDATE account_move '\
                           'SET state=%s '\
                           'WHERE id IN %s',
                           ('draft', tuple(valid_moves),))
        return return_value

    def button_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.period_id.state == 'done':
                raise osv.except_osv(_('Error'), _('You can not modify a posted entry of closed periods'))
            ## Change the test of line state instead of journal type
            elif line.state == 'posted':
                raise osv.except_osv(_('Error'), _('''You can not modify a posted entry of this journal!\n \
                You should set the journal to allow cancelling entries if you want to do that.'''))
        if ids:
            move_obj = self.pool.get('account.move')
            move_obj.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
