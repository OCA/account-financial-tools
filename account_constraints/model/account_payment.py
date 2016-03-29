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

from openerp import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _create_payment_entry(self, amount):
        """Override the method to add the key 'from_parent_object' in
        the context. This is to allow to delete move line related to
        bank statement through the cancel button.
        """
        self = self.with_context(from_parent_object=True)
        return super(AccountPayment, self)._create_payment_entry(amount)

    def _create_transfer_entry(self, amount):
        """Override the method to add the key 'from_parent_object' in
        the context. This is to allow to delete move line related to
        bank statement through the cancel button.
        """
        self = self.with_context(from_parent_object=True)
        return super(AccountPayment, self)._create_transfert_entry(amount)
