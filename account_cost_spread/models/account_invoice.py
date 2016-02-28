# -*- coding: utf-8 -*-
# © 2014 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        """Override, button Validate on invoices."""
        res = super(AccountInvoice, self).action_move_create()
        for rec in self:
            for line in rec.invoice_line:
                line.compute_spread_board()
        return res
