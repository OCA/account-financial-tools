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
from openerp import models, fields, api, _


class AccountInvoice(models.Model):
    """Check on cancelling of an invoice"""
    _inherit = 'account.invoice'

    credit_policy_id = fields.Many2one(
        'credit.control.policy',
        string='Credit Control Policy',
        help="The Credit Control Policy used for this "
             "invoice. If nothing is defined, it will "
             "use the account setting or the partner "
             "setting.",
        readonly=True,
        copy=False,
        groups="account_credit_control.group_account_credit_control_manager,"
               "account_credit_control.group_account_credit_control_user,"
               "account_credit_control.group_account_credit_control_info",
    )

    credit_control_line_ids = fields.One2many(
        'credit.control.line', 'invoice_id',
        string='Credit Lines',
        readonly=True,
        copy=False,
    )

    @api.multi
    def action_cancel(self):
        """Prevent to cancel invoice related to credit line"""
        # We will search if this invoice is linked with credit
        cc_line_obj = self.env['credit.control.line']
        for invoice in self:
            nondraft_domain = [('invoice_id', '=', invoice.id),
                               ('state', '!=', 'draft')]
            cc_nondraft_lines = cc_line_obj.search(nondraft_domain)
            if cc_nondraft_lines:
                raise api.Warning(
                    _('You cannot cancel this invoice.\n'
                      'A payment reminder has already been '
                      'sent to the customer.\n'
                      'You must create a credit note and '
                      'issue a new invoice.')
                )
            draft_domain = [('invoice_id', '=', invoice.id),
                            ('state', '=', 'draft')]
            cc_draft_line = cc_line_obj.search(draft_domain)
            cc_draft_line.unlink()
        return super(AccountInvoice, self).action_cancel()
