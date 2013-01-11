# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.osv import fields, osv
from openerp.osv.orm import Model
from openerp.tools.translate import _

class AccountMove(Model):
    _inherit = "account.move"

    def _check_fiscal_year(self, cursor, user, ids):
        for move in self.browse(cursor, user, ids):
            date_start = move.period_id.fiscalyear_id.date_start
            date_stop = move.period_id.fiscalyear_id.date_stop
            if move.date < date_start or move.date > date_stop:
                return False
        return True

    _constraints = [
        (_check_fiscal_year,
            'You cannot create entries with date not in the fiscal year of the chosen period',
            ['line_id','']),
    ]


class AccountMoveLine(Model):
    _inherit='account.move.line'
    
    def _check_currency_and_amount(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if (l.currency_id and not l.amount_currency) or (not l.currency_id and l.amount_currency):
                return False
        return True

    def _check_currency_amount(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if l.amount_currency:
                if (l.amount_currency > 0.0 and l.credit > 0.0) or (l.amount_currency < 0.0 and l.debit > 0.0):
                    return False
        return True

    def _check_currency_company(self, cr, uid, ids, context=None):
        for l in self.browse(cr, uid, ids, context=context):
            if l.currency_id.id == l.company_id.currency_id.id:
                return False
        return True

    _constraints = [
            (
                _check_currency_and_amount, 
                "You cannot create journal items with a secondary currency without recording \
                    both 'currency' and 'amount currency' field.",
                ['currency_id','amount_currency']
            ),
            (
                _check_currency_amount, 
                'The amount expressed in the secondary currency must be positif when journal item\
                 are debit and negatif when journal item are credit.', 
                 ['amount_currency']
            ),
            (
                _check_currency_company, 
                "You can't provide a secondary currency if the same than the company one." , 
                ['currency_id']
            ),
        ]
        

