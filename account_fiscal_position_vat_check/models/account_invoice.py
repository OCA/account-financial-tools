# © 2013-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        """Check that the customer has VAT set if required by the
        fiscal position"""
        for invoice in self:
            if (
                    invoice.type in ('out_invoice', 'out_refund') and
                    invoice.fiscal_position_id.vat_required and
                    not invoice.partner_id.vat):
                raise UserError(_(
                    "You are trying to validate a customer invoice/refund "
                    "with the fiscal position '%s' that require the customer "
                    "to have a VAT number. But the Customer '%s' doesn't have "
                    "a VAT number in Odoo. Please add the VAT number of this "
                    "Customer in Odoo and try to validate again.") % (
                        invoice.fiscal_position_id.name,
                        invoice.partner_id.name_get()[0][1]))
        return super(AccountInvoice, self).action_move_create()
