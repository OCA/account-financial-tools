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

import time

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp

class account_bank_statement(osv.osv):
    _inherit = "account.bank.statement"

    def create_move_from_st_line(self, cr, uid, st_line_id, company_currency_id, st_line_number, context=None):
        return_value = super(account_bank_statement,self).create_move_from_st_line(cr, uid, st_line_id, company_currency_id, st_line_number, context)
        ## We receive the move created for the bank statement, we set it to draft
        if return_value:
            cr.execute('UPDATE account_move '\
                       'SET state=%s '\
                       'WHERE id = %s', ('draft', (return_value),))
        return return_value


account_bank_statement()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
