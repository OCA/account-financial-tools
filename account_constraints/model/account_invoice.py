# -*- coding: utf-8 -*-
# © 2012, Joel Grand-Guillaume, Camptocamp SA.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


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
