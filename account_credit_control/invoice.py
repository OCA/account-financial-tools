# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Vincent Renaville
#    Copyright 2013 Camptocamp SA
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
from openerp.tools.translate import _


class AccountInvoice(orm.Model):
    """Check on cancelling of an invoice"""
    _inherit = 'account.invoice'

    _columns = {
        'credit_policy_id':
            fields.many2one('credit.control.policy',
                            'Credit Control Policy',
                            help=("The Credit Control Policy used for this "
                                  "invoice. If nothing is defined, it will "
                                  "use the account setting or the partner "
                                  "setting."),
                            readonly=True,
                            ),
        'credit_control_line_ids':
            fields.one2many('credit.control.line',
                            'invoice_id',
                            string='Credit Lines',
                            readonly=True),
        }

    def copy_data(self, cr, uid, id, default=None, context=None):
        """Ensure that credit lines and policy are not copied"""
        if default is None:
            default = {}
        else:
            default = default.copy()
        default = default.copy()
        default['credit_control_line_ids'] = False
        default['credit_policy_id'] = False
        return super(AccountInvoice, self).copy_data(
            cr, uid, id, default=default, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        """Prevent to cancel invoice related to credit line"""
        # We will search if this invoice is linked with credit
        cc_line_obj = self.pool.get('credit.control.line')
        for invoice_id in ids:
            cc_nondraft_line_ids = cc_line_obj.search(
                cr, uid,
                [('invoice_id', '=', invoice_id),
                 ('state', '<>', 'draft')],
                context=context)
            if cc_nondraft_line_ids:
                raise orm.except_orm(_('Error!'),
                                     _('You cannot cancel this invoice.\n'
                                       'A payment reminder has already been '
                                       'sent to the customer.\n'
                                       'You must create a credit note and '
                                       'issue a new invoice.'))
            cc_draft_line_ids = cc_line_obj.search(
                cr, uid,
                [('invoice_id', '=', invoice_id),
                 ('state', '=', 'draft')],
                context=context)
            cc_line_obj.unlink(cr, uid,
                               cc_draft_line_ids,
                               context=context)
        return super(AccountInvoice, self).action_cancel(cr, uid, ids,
                                                         context=context)
