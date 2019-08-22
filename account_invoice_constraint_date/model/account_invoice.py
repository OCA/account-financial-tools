# -*- coding: utf-8 -*-
# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>

from odoo import models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.type in ('in_invoice', 'in_refund'):
                if inv.date_invoice and inv.date and \
                        inv.date_invoice > inv.date:
                    raise UserError(
                        _("The invoice date cannot be later than"
                          " the date of registration!"))
        return res
