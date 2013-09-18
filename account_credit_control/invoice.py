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

    def action_cancel(self, cr, uid, ids, context=None):
        # We will search if this invoice is linked with credit
        credit_control_line_obj = self.pool.get('credit.control.line')
        for invoice_id in ids:
            credit_control_line_ids_nondraft = credit_control_line_obj.search(cr,
                                                                              uid,
                                                                              [('invoice_id', '=', invoice_id),
                                                                               ('state', '<>', 'draft')],context=context)
            if credit_control_line_ids_nondraft:
                raise orm.except_orm(_('Error!'),
                                     _('You cannot cancel this invoice ! '
                                       'A payment reminder has already been '
                                       'sent to the customer.'
                                       'You must create a credit note and raise a new invoice.'))
            credit_control_line_ids_draft = credit_control_line_obj.search(cr,
                                                                           uid,
                                                                           [('invoice_id', '=', invoice_id),
                                                                            ('state', '=', 'draft')],context=context)
            if credit_control_line_ids_draft:
                credit_control_line_obj.unlink(cr,
                                               uid,
                                               credit_control_line_ids_draft,
                                               context=context)
        return super(AccountInvoice, self).action_cancel(cr,
                                                         uid,
                                                         ids,
                                                         context=context)
