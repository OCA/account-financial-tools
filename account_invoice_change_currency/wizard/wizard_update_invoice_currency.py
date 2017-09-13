# -*- coding: utf-8 -*-
# © 2015 Eficent
# © 2015 Techrifiv Solutions Pte Ltd
# © 2015 Statecraft Systems Pte Ltd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models, fields


class WizardUpdateInvoiceCurrency(models.TransientModel):

    _name = 'wizard.update.invoice.currency'

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True)

    @api.multi
    def button_update_currency(self):
        self.ensure_one()
        invoice = self.env['account.invoice'].browse(
            self._context.get('active_id'))
        if invoice and invoice.currency_id != self.currency_id:
            from_currency = invoice.currency_id
            for line in invoice.invoice_line_ids:
                line.price_unit = from_currency.compute(
                    line.price_unit, self.currency_id)

            for tax in invoice.tax_line_ids:
                tax.amount = from_currency.compute(
                    tax.amount, self.currency_id)

            invoice.currency_id = self.currency_id

        return True
