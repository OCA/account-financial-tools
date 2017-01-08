# -*- coding: utf-8 -*-
# © 2013-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import except_orm


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    customer_must_have_vat = fields.Boolean(
        string='Customer Must Have VAT number',
        help="If enabled, Odoo will check that the customer has a VAT "
        "number when the user validates a customer invoice/refund.")


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        '''Check that the customer has VAT set
        if required by the fiscal position'''
        for invoice in self:
            if (
                    invoice.type in ('out_invoice', 'out_refund') and
                    invoice.fiscal_position and
                    invoice.fiscal_position.customer_must_have_vat and
                    not invoice.partner_id.vat):
                if invoice.type == 'out_invoice':
                    type_label = _('a Customer Invoice')
                else:
                    type_label = _('a Customer Refund')
                raise except_orm(
                    _('Missing VAT number:'),
                    _("You are trying to validate %s "
                      "with the fiscal position '%s' "
                      "that require the customer to have a VAT number. "
                      "But the Customer '%s' doesn't "
                      "have a VAT number in OpenERP."
                      "Please add the VAT number of this Customer in Odoo "
                      " and try to validate again.")
                    % (type_label, invoice.fiscal_position.name,
                        invoice.partner_id.name))
        return super(AccountInvoice, self).action_move_create()
