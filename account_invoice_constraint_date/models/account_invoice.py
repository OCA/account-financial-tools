# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        res = super().action_move_create()
        for inv in self:
            if inv.type in ('in_invoice', 'in_refund'):
                if inv.date_invoice and inv.date and \
                        inv.date_invoice > inv.date:
                    raise UserError(
                        _("The invoice date cannot be later than"
                          " the date of registration!"))
        return res
