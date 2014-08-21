# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume. Copyright 2012 Camptocamp SA
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

from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_cancel(self):
        """Override the method to add the key 'from_parent_object' in
        the context. This is to allow to delete move line related to
        invoice through the cancel button.
        """
        self = self.with_context(from_parent_object=True)
        return super(AccountInvoice, self).action_cancel()

    @api.multi
    def action_move_create(self):
        """Override the method to add the key 'from_parent_object' in
        the context."""
        self = self.with_context(from_parent_object=True)
        return super(AccountInvoice, self).action_move_create()
