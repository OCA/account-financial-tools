# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
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
#
##############################################################################
from openerp.osv import orm, fields


class AccountAccount(orm.Model):
    """Add a link to a credit control policy on account.account"""

    _inherit = "account.account"

    _columns = {'credit_control_line_ids': fields.one2many('credit.control.line',
                                                           'account_id',
                                                           string='Credit Lines',
                                                           readonly=True)
                }


class AccountInvoice(orm.Model):
    """Add a link to a credit control policy on account.account"""

    _inherit = "account.invoice"
    _columns = {'credit_policy_id': fields.many2one('credit.control.policy',
                                                    'Credit Control Policy',
                                                    help=("The Credit Control Policy "
                                                          "used for this invoice. "
                                                          "If nothing is defined, "
                                                          "it will use the account "
                                                          "setting or the partner "
                                                          "setting.")),

                'credit_control_line_ids': fields.one2many('credit.control.line',
                                                           'invoice_id',
                                                           string='Credit Lines',
                                                           readonly=True)
                }

    def action_move_create(self, cr, uid, ids, context=None):
        """ Write the id of the invoice in the generated moves. """
        if context is None:
            context = {}
        # add from_parent_object to the conxtext to let the line.write
        # call pass through account_constraints
        ctxt = context.copy()
        ctxt['from_parent_object'] = True
        res = super(AccountInvoice, self).action_move_create(cr, uid, ids, context=ctxt)
        for inv in self.browse(cr, uid, ids, context=ctxt):
            if inv.move_id:
                for line in inv.move_id.line_id:
                    line.write({'invoice_id': inv.id}, context=ctxt)
        return res


class AccountMoveLine(orm.Model):

    _inherit = "account.move.line"

    _columns = {'invoice_id': fields.many2one('account.invoice', 'Invoice')}
