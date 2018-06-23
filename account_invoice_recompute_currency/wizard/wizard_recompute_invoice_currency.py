# -*- coding: utf-8 -*-
# Copyright 2017 Komit <http://komit-consulting.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models, fields


class WizardRecomputeInvoiceCurrency(models.TransientModel):

    _name = 'wizard.recompute.invoice.currency'

    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        help='Choose the currency you want to change', required=True)

    @api.multi
    def button_recompute_currency(self):
        self.ensure_one()
        invoice = self.env['account.invoice'].browse(
            self._context.get('active_id'))
        if invoice and invoice.currency_id != self.currency_id:
            from_currency = invoice.currency_id

            for line in invoice.invoice_line_ids:
                line.price_unit = from_currency.with_context(
                    date=invoice.date_invoice).compute(
                    line.price_unit, self.currency_id)

            for tax in invoice.tax_line_ids:
                tax.amount = from_currency.with_context(
                    date=invoice.date_invoice).compute(
                    tax.amount, self.currency_id)

            invoice.currency_id = self.currency_id

        return True
